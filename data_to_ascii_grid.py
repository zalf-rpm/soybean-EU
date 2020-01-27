#!/usr/bin/python
# -*- coding: UTF-8

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/. */

# This file has been created at the Institute of
# Landscape Systems Analysis at the ZALF.
# Copyright (C: Leibniz Centre for Agricultural Landscape Research (ZALF)

import sys
import os
import math
import statistics 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.backends.backend_pdf import PdfPages

PATHS = {
    "local": {
        "sim-result-path": "./out/", # path to simulation results
        "ascii-out" : "./asciigrids/" , # path to ascii grids
        "png-out" : "./png/" , # path to png images
        "pdf-out" : "./pdf-out/" , # path to pdf package
    },
    "test": {
        "sim-result-path": "./out2/", # path to simulation results
        "ascii-out" : "./asciigrids2/" , # path to ascii grids
        "png-out" : "./png2/" , # path to png images
        "pdf-out" : "./pdf-out2/" , # path to pdf package
    },
    "nolimit": {
        "sim-result-path": "./out/", # path to simulation results
        "ascii-out" : "./asciigrid_nolimit/" , # path to ascii grids
        "png-out" : "./png_nolimit/" , # path to png images
        "pdf-out" : "./pdf-out_nolimit/" , # path to pdf package
    }
}

ASCII_OUT_FILENAME_FROST = "frostred_{0}_trno{1}.asc" # mGroup_treatmentnumber 
ASCII_OUT_FILENAME_AVG = "avg_{0}_trno{1}.asc" # mGroup_treatmentnumber 
ASCII_OUT_FILENAME_DEVI_AVG = "devi_avg_{0}_trno{1}.asc" # mGroup_treatmentnumber
ASCII_OUT_FILENAME_MAX_YIELD = "maxyield_trno{0}.asc" # treatmentnumber 
ASCII_OUT_FILENAME_MAX_YIELD_MAT = "maxyield_matgroup_trno{0}.asc" # treatmentnumber 
ASCII_OUT_FILENAME_FROST_DIFF = "frost_diff_{0}.asc" # sort
ASCII_OUT_FILENAME_FROST_DIFF_MAX = "frost_diff_max_yield.asc" 
ASCII_OUT_FILENAME_WATER_DIFF = "water_diff_{0}.asc" # sort
ASCII_OUT_FILENAME_WATER_DIFF_MAX = "water_diff_max_yield.asc" 

CELLFORMAT="{0} "
USER = "local" 
BASEFILENAME = "EU_SOY_MO_"
CROPNAME = "soybean"
NONEVALUE = -9999

def calculateGrid() :
    "main"

    pathId = USER
    if len(sys.argv) > 1 and __name__ == "__main__":
        for arg in sys.argv[1:]:
            k, v = arg.split("=")
            if k == "path":
                pathId = v

    inputFolder = PATHS[pathId]["sim-result-path"]
    asciiOutFolder = PATHS[pathId]["ascii-out"]
    pngFolder = PATHS[pathId]["png-out"]
    pdfFolder = PATHS[pathId]["pdf-out"]
    errorFile = os.path.join(asciiOutFolder, "error.txt")

    filelist = os.listdir(inputFolder)

    # get grid extension
    extCol = 0
    extRow = 0
    idxFileDic = dict()
    for filename in filelist: 
        grid = GetGridfromFilename(filename)
        if grid[0] == -1 :
            continue
        else : 
            if extRow < grid[0] :
                extRow = grid[0]
            if extCol < grid[1] :
                extCol = grid[1]

        #indexed file list by grid, remove all none csv        
        idxFileDic[grid] = filename

    maxAllAvgYield = 0
    maxSdtDeviation = 0
    maxVarFrost = 0 
    numInput = len(idxFileDic)
    currentInput = 0
    allGrids = dict()
    StdDevAvgGrids = dict()
    allFrostGrids = dict()
    outputFilesGenerated = False
    # iterate over all grid cells 
    for currRow in range(1, extRow+1) :
        for currCol in range(1, extCol+1) :
            gridIndex = (currRow, currCol)
            if gridIndex in idxFileDic :
                # open grid cell file
                with open(os.path.join(inputFolder, idxFileDic[gridIndex])) as sourcefile:
                    simulations = dict()
                    frostSim = dict()
                    firstLine = True
                    header = list()
                    for line in sourcefile:
                        if firstLine :
                            # read header
                            firstLine = False
                            header = ReadHeader(line)
                        else :
                            # load relevant line content
                            lineContent = loadLine(line, header)
                            # check for the lines with a specific crop
                            if IsCrop(lineContent, CROPNAME) :
                                lineKey = (lineContent[:-2])
                                yieldValue = lineContent[-1]
                                frostRed = lineContent[-2]
                                if not lineKey in simulations :
                                    simulations[lineKey] = list() 
                                    frostSim[lineKey] = list() 
                                frostSim[lineKey].append(frostRed)
                                simulations[lineKey].append(yieldValue)

                    if not outputFilesGenerated :
                        outputFilesGenerated = True
                        for simKey in simulations :
                            allGrids[simKey] =  newGrid(extRow, extCol, NONEVALUE)
                            StdDevAvgGrids[simKey] =  newGrid(extRow, extCol, NONEVALUE)
                            allFrostGrids[simKey] =  newGrid(extRow, extCol, NONEVALUE)

                    for simKey in simulations :
                        pixelValue = CalculatePixel(simulations[simKey])
                        if pixelValue > maxAllAvgYield :
                            maxAllAvgYield = pixelValue

                        stdDeviation = statistics.stdev(simulations[simKey])
                        if stdDeviation > maxSdtDeviation :
                            maxSdtDeviation = stdDeviation
                        hasFrost = average(frostSim[simKey])
                        if maxVarFrost < hasFrost :
                            maxVarFrost = hasFrost
                        #if any(x < 1.0 for x in frostSim[simKey]) :
                        #    statistics.variance()
                        #    hasFrost = 1
                            #WriteError(errorFile, "Frost {0} {1} {2} {3}".format(idxFileDic[gridIndex], simKey, frostSim[simKey], simulations[simKey])) 

                        allGrids[simKey][currRow-1][currCol-1] = int(pixelValue)
                        StdDevAvgGrids[simKey][currRow-1][currCol-1] = int(stdDeviation)
                        allFrostGrids[simKey][currRow-1][currCol-1] = hasFrost
                    currentInput += 1 
                    progress(currentInput, numInput, str(currentInput) + " of " + str(numInput))

            else :
                continue
    
    pdfList = dict()
    for simKey in allGrids :
        if not simKey[1] in pdfList : 
            pdfpath = os.path.join(pdfFolder, "scenario_{0}.pdf".format(simKey[1]))
            makeDir(pdfpath)
            pdfList[simKey[1]] = PdfPages(pdfpath)

    #write average yield grid 
    currentInput = 0
    numInput = len(allGrids)
    for simKey in allGrids :
        # ASCII_OUT_FILENAME_AVG = "avg_{0}_trno{1}.asc" # mGroup_treatmentnumber 
        gridFileName = ASCII_OUT_FILENAME_AVG.format(simKey[2], simKey[0])
        gridFileName = gridFileName.replace("/", "-") #remove directory seperator from filename
        gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
        #treatmentNoIdx, climateSenarioCIdx, mGroupCIdx, yieldsCIdx
        file = writeAGridHeader(gridFilePath, extCol, extRow, maxValue=maxAllAvgYield)
        for row in range(extRow-1, -1, -1) :
            seperator = ' '
            file.write(seperator.join(map(str, allGrids[simKey][row])) + "\n")
        file.close()
        # create png
        pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
        title = "Average Yield - Scenario {0} {1} {2}".format(simKey[1], simKey[2], simKey[3])
        createImg(gridFilePath, pngFilePath, title, label='Yield in t', pdf=pdfList[simKey[1]])
        currentInput += 1 
        progress(currentInput, numInput, str(currentInput) + " of " + str(numInput) + " average yield grids     ")

    currentInput = 0
    numInput = len(allFrostGrids)
    #cDualMap = ListedColormap(['cyan','magenta'])
    for simKey in allFrostGrids :
        # ASCII_OUT_FILENAME_AVG = "avg_{0}_trno{1}.asc" # mGroup_treatmentnumber 
        gridFileName = ASCII_OUT_FILENAME_FROST.format(simKey[2], simKey[0])
        gridFileName = gridFileName.replace("/", "-") #remove directory seperator from filename
        gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
        #treatmentNoIdx, climateSenarioCIdx, mGroupCIdx, yieldsCIdx
        file = writeAGridHeader(gridFilePath, extCol, extRow, maxValue=maxVarFrost)
        for row in range(extRow-1, -1, -1) :
            seperator = ' '
            file.write(seperator.join(map(str, allFrostGrids[simKey][row])) + "\n")
        file.close()
        # create png
        pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
        title = "Frost Redution - Scenario {0} {1} {2}".format(simKey[1], simKey[2], simKey[3])
        createImg(gridFilePath, pngFilePath, title, label='Frost reduction', colormap='winter', factor=1, pdf=pdfList[simKey[1]])
        currentInput += 1 
        progress(currentInput, numInput, str(currentInput) + " of " + str(numInput) + " frost grid     ")

    currentInput = 0
    numInput = len(StdDevAvgGrids)
    for simKey in StdDevAvgGrids :
        # ASCII_OUT_FILENAME_DEVI_AVG = "devi_avg_{0}_trno{1}.asc" # mGroup_treatmentnumber
        gridFileName = ASCII_OUT_FILENAME_DEVI_AVG.format(simKey[2], simKey[0])
        gridFileName = gridFileName.replace("/", "-") #remove directory seperator from filename
        gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
        file = writeAGridHeader(gridFilePath, extCol, extRow, maxValue=maxSdtDeviation) 
        for row in range(extRow-1, -1, -1) :
            seperator = ' '
            file.write(seperator.join(map(str, StdDevAvgGrids[simKey][row])) + "\n")
        file.close()

        # create png
        pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
        title = "Std Deviation - Scenario {0} {1} {2}".format(simKey[1], simKey[2], simKey[3])
        createImg(gridFilePath, pngFilePath, title, label='standart deviation', colormap='cool', factor=1, pdf=pdfList[simKey[1]])
        currentInput += 1 
        progress(currentInput, numInput, str(currentInput) + " of " + str(numInput) + " std deviation grids           ")

    ### Start calculate max yield layer and maturity layer grid 
    maxYieldGrids = dict()
    matGroupGrids = dict()
    matGroupIdGrids = dict()
    matIdcounter = 0    
    matGroupIdGrids["none"] = matIdcounter # maturity group id for 'no yield'
    for simKey in allGrids :
        #treatmentNoIdx, climateSenarioCIdx, mGroupCIdx, yieldsCIdx
        scenarioKey = (simKey[0], simKey[1], simKey[3])
        if not scenarioKey in maxYieldGrids :
            maxYieldGrids[scenarioKey] = newGrid(extRow, extCol, NONEVALUE)
            matGroupGrids[scenarioKey] = newGrid(extRow, extCol, NONEVALUE)
        currGrid = allGrids[simKey]

        for row in range(extRow) :
            for col in range(extCol) :
                if currGrid[row][col] > maxYieldGrids[scenarioKey][row][col] :
                    maxYieldGrids[scenarioKey][row][col] = currGrid[row][col]
                    # set ids for each maturity group
                    if not simKey[2] in matGroupIdGrids :
                        matIdcounter += 1
                        matGroupIdGrids[simKey[2]] = matIdcounter
                    if currGrid[row][col] == 0 :
                        matGroupGrids[scenarioKey][row][col] = matGroupIdGrids["none"]
                    else :
                        matGroupGrids[scenarioKey][row][col] = matGroupIdGrids[simKey[2]]

    currentInput = 0
    numInput = len(maxYieldGrids)
    for simKey in maxYieldGrids :
        # ASCII_OUT_FILENAME_MAX_YIELD = "maxyield_trno{1}.asc" # treatmentnumber 
        gridFileName = ASCII_OUT_FILENAME_MAX_YIELD.format(simKey[0])
        gridFileName = gridFileName.replace("/", "-") #remove directory seperator from filename
        gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
        # create ascii file
        file = writeAGridHeader(gridFilePath, extCol, extRow, maxValue = maxAllAvgYield)
        for row in range(extRow-1, -1, -1) :
            seperator = ' '
            file.write(seperator.join(map(str, maxYieldGrids[simKey][row])) + "\n")
        file.close()
        # create png
        pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
        title = "Max average yield - Scenario {0} {1}".format(simKey[1], simKey[2])
        createImg(gridFilePath, pngFilePath, title, label='Yield in t', colormap='jet', pdf=pdfList[simKey[1]])
        currentInput += 1 
        progress(currentInput, numInput, str(currentInput) + " of " + str(numInput) + " max yields grids      ")

    currentInput = 0
    numInput = len(matGroupGrids)
    sidebarLabel = ["none"] * len(matGroupIdGrids)
    cMap = ListedColormap(['cyan', 'lightgreen', 'magenta','crimson', 'blue','gold', 'navy'])
    for id in matGroupIdGrids :
        sidebarLabel[matGroupIdGrids[id]] = id
    for simKey in matGroupGrids :
        # ASCII_OUT_FILENAME_MAX_YIELD_MAT = "maxyield_matgroup_trno{1}.asc" # treatmentnumber 
        gridFileName = ASCII_OUT_FILENAME_MAX_YIELD_MAT.format(simKey[0])
        gridFileName = gridFileName.replace("/", "-") #remove directory seperator from filename
        gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
        # create ascii file
        file = writeAGridHeader(gridFilePath, extCol, extRow)
        for row in range(extRow-1, -1, -1) :
            seperator = ' '
            file.write(seperator.join(map(str, matGroupGrids[simKey][row])) + "\n")
        file.close()
        # create png
        pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
        title = "Maturity groups for max average yield - Scenario {0} {1}".format(simKey[1], simKey[2])
        createImg(gridFilePath, pngFilePath, title, label='Maturity Group', colormap=cMap, factor=1, cbarLabel=sidebarLabel, pdf=pdfList[simKey[1]])
        currentInput += 1 
        progress(currentInput, numInput, str(currentInput) + " of " + str(numInput) + " mat groups grids          ")

    #### END calculate max yield layer and maturity layer grid 

    #### Grid Diff affected by frost T4(potential) - T2(unlimited water) 
    currentInput = 0
    numInput = len(allGrids)
    for simKey in allGrids :
        # treatment number
        if simKey[0] == "T2" :
            otherKey = ("T4",simKey[1], simKey[2], "Potential")
            newDiffGrid = GridDifference(allGrids[otherKey], allGrids[simKey], extRow, extCol)
            
            gridFileName = ASCII_OUT_FILENAME_FROST_DIFF.format(simKey[2])
            gridFileName = gridFileName.replace("/", "-") #remove directory seperator from filename
            gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
            # create ascii file
            file = writeAGridHeader(gridFilePath, extCol, extRow, maxValue=maxAllAvgYield)
            for row in range(extRow-1, -1, -1) :
                seperator = ' '
                file.write(seperator.join(map(str, newDiffGrid[row])) + "\n")
            file.close()
            # create png
            pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
            title = "Frost effect on potential yield - Scenario {0} {1}".format(simKey[1], simKey[2])
            createImg(gridFilePath, pngFilePath, title, label='Difference yield in t', colormap='summer', pdf=pdfList[simKey[1]])
            currentInput += 1 
            progress(currentInput, numInput, str(currentInput) + " of " + str(numInput) + " frost diff grids      ")
    
    currentInput = 0
    numInput = len(maxYieldGrids)
    for simKey in maxYieldGrids :
        # treatment number
        if simKey[0] == "T2" :
            otherKey = ("T4",simKey[1], "Potential")
            newDiffGrid = GridDifference(maxYieldGrids[otherKey], maxYieldGrids[simKey], extRow, extCol)
            
            gridFileName = ASCII_OUT_FILENAME_FROST_DIFF_MAX
            gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
            # create ascii file
            file = writeAGridHeader(gridFilePath, extCol, extRow, maxValue=maxAllAvgYield)
            for row in range(extRow-1, -1, -1) :
                seperator = ' '
                file.write(seperator.join(map(str, newDiffGrid[row])) + "\n")
            file.close()
            # create png
            pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
            title = "Frost effect on potential max yield - Scenario {0}".format(simKey[1])
            createImg(gridFilePath, pngFilePath, title, label='Difference yield in t', colormap='summer', pdf=pdfList[simKey[1]])
            currentInput += 1 
            progress(currentInput, numInput, str(currentInput) + " of " + str(numInput) + " frost diff grids max      ")


    #### Grid Diff affected by water stress T4(potential) - T3(no frost) 
    currentInput = 0
    numInput = len(allGrids)
    for simKey in allGrids :
        # treatment number
        if simKey[0] == "T3" :
            otherKey = ("T4",simKey[1], simKey[2], "Potential")
            newDiffGrid = GridDifference(allGrids[otherKey], allGrids[simKey], extRow, extCol)
            
            gridFileName = ASCII_OUT_FILENAME_WATER_DIFF.format(simKey[2])
            gridFileName = gridFileName.replace("/", "-") #remove directory seperator from filename
            gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
            # create ascii file
            file = writeAGridHeader(gridFilePath, extCol, extRow, maxValue=maxAllAvgYield)
            for row in range(extRow-1, -1, -1) :
                seperator = ' '
                file.write(seperator.join(map(str, newDiffGrid[row])) + "\n")
            file.close()
            # create png
            pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
            title = "Water stress effect on potential yield - Scenario {0} {1}".format(simKey[1], simKey[2])
            createImg(gridFilePath, pngFilePath, title, label='Difference yield in t', colormap='Wistia', pdf=pdfList[simKey[1]])
            currentInput += 1 
            progress(currentInput, numInput, str(currentInput) + " of " + str(numInput) + " water diff grids         ")

    currentInput = 0
    numInput = len(maxYieldGrids)
    for simKey in maxYieldGrids :
        # treatment number
        if simKey[0] == "T3" :
            otherKey = ("T4",simKey[1], "Potential")
            newDiffGrid = GridDifference(maxYieldGrids[otherKey], maxYieldGrids[simKey], extRow, extCol)
            
            gridFileName = ASCII_OUT_FILENAME_WATER_DIFF_MAX
            gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
            # create ascii file
            file = writeAGridHeader(gridFilePath, extCol, extRow, maxValue=maxAllAvgYield)
            for row in range(extRow-1, -1, -1) :
                seperator = ' '
                file.write(seperator.join(map(str, newDiffGrid[row])) + "\n")
            file.close()
            # create png
            pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
            title = "Water stress  effect on potential max yield - Scenario {0}".format(simKey[1])
            createImg(gridFilePath, pngFilePath, title, label='Difference yield in t', colormap='Wistia', pdf=pdfList[simKey[1]])
            currentInput += 1 
            progress(currentInput, numInput, str(currentInput) + " of " + str(numInput) + " water diff grids max      ")

    for simKey in pdfList :
        pdfList[simKey].close()

def newGrid(extRow, extCol, defaultVal) :
    grid = [defaultVal] * extRow
    for i in range(extRow) :
        grid[i] = [defaultVal] * extCol
    return grid

def CalculatePixel(yieldList) :
    pixelValue = average(yieldList)
    if HasUnStableYield(yieldList, pixelValue) : 
        pixelValue = 0
    return pixelValue

# adjust this methode to define if yield loss is too hight
def HasUnStableYield(yieldList, averageValue) :
    unstable = False
    counter = 0
    lowPercent = averageValue * 0.2
    for y in yieldList :
        if y < 900 or y < lowPercent: 
            counter +=1
    if counter > 1 :
        unstable = True
    return unstable

def ReadHeader(line) : 
    #read header
    tokens = line.split(",")
    i = -1
    for token in tokens :
        i = i+1
        if token == "Crop":
            mGroupCIdx = i
        if token == "sce":
            climateSenarioCIdx = i
        if token == "Yield" : 
            yieldsCIdx = i
        if token == "ProductionCase":
            commentIdx = i
        if token == "TrtNo" : 
            treatNoIdx = i
        if token == "frostred" : 
            frostRedIdx = i

    return (treatNoIdx, climateSenarioCIdx, mGroupCIdx, commentIdx, frostRedIdx, yieldsCIdx)

def IsCrop(key, cropName) :
    return key[2].startswith(cropName) 
    
# read relevant content from line 
def loadLine(line, header) :
    tokens = line.split(",")
    treatNo = tokens[header[0]] # some ID
    climateSenario = tokens[header[1]] # some ID
    mGroup = tokens[header[2]] # some ID
    comment = tokens[header[3]]
    frostRed = float(tokens[header[4]])
    yields = float(tokens[header[5]]) # 12345

    return (treatNo, climateSenario, mGroup, comment, frostRed, yields)

def GridDifference(grid1, grid2, extRow, extCol) :
    newGridDiff = newGrid(extRow, extCol, NONEVALUE) 
    for row in range(extRow) :
        for col in range(extCol) :
            if  grid1[row][col] != NONEVALUE: 
                newGridDiff[row][col] = grid1[row][col] - grid2[row][col]
            else :
                newGridDiff[row][col] = NONEVALUE
    return newGridDiff

def GetGridfromFilename(filename) :
    basename = os.path.basename(filename)
    rol_col_tuple = (-1,-1)
    if basename.endswith(".csv") and basename.startswith(BASEFILENAME) :
        basename = basename[:-4]
        basename = basename[len(BASEFILENAME):]
        tokens = basename.split("_", 1) 
        if len(tokens) == 2 :
            row = int(tokens[0])
            col = int(tokens[1])
            rol_col_tuple = (row,col)

    return rol_col_tuple


def writeAGridHeader(name, nCol, nRow, cornerX=0.0, cornery=0.0, novalue=-9999, cellsize=1.0, maxValue=-9999) :
    
    makeDir(name)

    file=open(name,"w")
    file.write("ncols {0}\n".format(nCol))
    file.write("nrows {0}\n".format(nRow))
    file.write("xllcorner     {0}\n".format(cornerX))
    file.write("yllcorner     {0}\n".format(cornery))
    file.write("cellsize      {0}\n".format(cellsize))
    file.write("NODATA_value  {0}\n".format(novalue))

    file.write("{0} ".format(maxValue))
    for i in range(1,nCol) :
        file.write(" {0}".format(novalue))
    file.write("\n".format(novalue))
    return file

def average(list) :
    val = 0.0
    if len(list) > 0 :
        val = sum(list) / len(list)

    return val

def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

def WriteError(filename, errorMsg) :
    f=open(filename, "a+")
    f.write("Error: " + errorMsg + "\r\n")
    f.close()

def createImg(prism_path, out_path, title, label='Yield in t', colormap='viridis', factor=0.001, cbarLabel=None, pdf=None) :
    # Read in PRISM header data
    with open(prism_path, 'r') as prism_f:
        prism_header = prism_f.readlines()[:6]
    
    # Read the PRISM ASCII raster header
    prism_header = [item.strip().split()[-1] for item in prism_header]
    prism_cols = int(prism_header[0])
    prism_rows = int(prism_header[1])
    prism_xll = float(prism_header[2])
    prism_yll = float(prism_header[3])
    prism_cs = float(prism_header[4])
    prism_nodata = float(prism_header[5])
    
    # Read in the PRISM array
    prism_array = np.loadtxt(prism_path, dtype=np.float, skiprows=6)
    
    # Set the nodata values to nan
    prism_array[prism_array == prism_nodata] = np.nan
    
    # PRISM data is stored as an integer but scaled by 100
    prism_array *= factor

    prism_extent = [
        prism_xll, prism_xll + prism_cols * prism_cs,
        prism_yll, prism_yll + prism_rows * prism_cs]
    
    # Plot PRISM array again
    fig, ax = plt.subplots()
    ax.set_title(title)
    
    # Get the img object in order to pass it to the colorbar function
    img_plot = ax.imshow(prism_array, cmap=colormap, extent=prism_extent)

    if cbarLabel :
        tick = 0.5 - len(cbarLabel) / 100 
        tickslist = [tick] * len(cbarLabel)
        for i in range(len(cbarLabel)) :
            tickslist[i] += i * 2 * tick

        # Place a colorbar next to the map
        cbar = plt.colorbar(img_plot, ticks=tickslist, orientation='vertical', shrink=0.5, aspect=14)
    else :
        # Place a colorbar next to the map
        cbar = plt.colorbar(img_plot, orientation='vertical', shrink=0.5, aspect=14)
    cbar.set_label(label)
    if cbarLabel :
        cbar.ax.set_yticklabels(cbarLabel) 

    ax.grid(True, alpha=0.5)

    makeDir(out_path)
    if pdf :
        pdf.savefig()
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    
def makeDir(out_path) :
    if not os.path.exists(os.path.dirname(out_path)):
        try:
            os.makedirs(os.path.dirname(out_path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

if __name__ == "__main__":
    calculateGrid()
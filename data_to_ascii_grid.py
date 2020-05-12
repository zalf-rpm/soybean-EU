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
import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import collections
import errno
from ruamel_yaml import YAML

PATHS = {
    "local": {
        "projectdatapath" : "./",
        "sourcepath" : "./source/",
        "outputpath" : ".",
        "climate-data" : "climate/transformed/" , # path to climate data
        "ascii-out" : "asciigrids_debug/" , # path to ascii grids
        "png-out" : "png_debug/" , # path to png images
        "pdf-out" : "pdf-out_debug/" , # path to pdf package
    },
    "test": {
        "projectdatapath" : "./",
        "sourcepath" : "./source/",
        "outputpath" : "./testout/",
        "climate-data" : "./climate-data/transformed/" , # path to climate data
        "ascii-out" : "asciigrids2/" , # path to ascii grids
        "png-out" : "png2/" , # path to png images
        "pdf-out" : "pdf-out2/" , # path to pdf package
    },
    "cluster": {
        "projectdatapath" : "/project/",
        "sourcepath" : "/source/",
        "outputpath" : "/out/",
        "climate-data" : "/climate-data/" , # path to climate data
        "ascii-out" : "asciigrid/" , # path to ascii grids
        "png-out" : "png/" , # path to png images
        "pdf-out" : "pdf-out/" , # path to pdf package
    }
}

ASCII_OUT_FILENAME_AVG = "avg_{0}_trno{1}.asc" # mGroup_treatmentnumber 
ASCII_OUT_FILENAME_DEVI_AVG = "devi_avg_{0}_trno{1}.asc" # mGroup_treatmentnumber
ASCII_OUT_FILENAME_MAX_YIELD = "maxyield_trno{0}.asc" # treatmentnumber 
ASCII_OUT_FILENAME_MAX_YIELD_MAT = "maxyield_matgroup_trno{0}.asc" # treatmentnumber 
ASCII_OUT_FILENAME_MAX_YIELD_DEVI = "maxyield_devi_trno{0}.asc" # treatmentnumber 
ASCII_OUT_FILENAME_MAX_YIELD_MAT_DEVI = "maxyield_devi_matgroup_trno{0}.asc" # treatmentnumber 
ASCII_OUT_FILENAME_WATER_DIFF = "water_diff_{0}.asc" # sort
ASCII_OUT_FILENAME_WATER_DIFF_MAX = "water_diff_max_yield.asc"
ASCII_OUT_FILENAME_SOW_DOY = "doy_sow_{0}_trno{1}.asc" # mGroup_treatmentnumber  
ASCII_OUT_FILENAME_EMERGE_DOY = "doy_emg_{0}_trno{1}.asc" # mGroup_treatmentnumber 
ASCII_OUT_FILENAME_ANTHESIS_DOY = "doy_ant_{0}_trno{1}.asc" # mGroup_treatmentnumber 
ASCII_OUT_FILENAME_MAT_DOY = "doy_mat_{0}_trno{1}.asc" # mGroup_treatmentnumber 
ASCII_OUT_FILENAME_COOL_WEATHER = "coolweather_{0}_trno{1}.asc" # mGroup_treatmentnumber 
ASCII_OUT_FILENAME_COOL_WEATHER_DEATH = "coolweather_severity_{0}_trno{1}.asc" # mGroup_treatmentnumber 
ASCII_OUT_FILENAME_COOL_WEATHER_WEIGHT = "coolweather_weights_{0}_trno{1}.asc" # mGroup_treatmentnumber 
ASCII_OUT_FILENAME_WET_HARVEST      = "harvest_wet_{0}_trno{1}.asc" # mGroup_treatmentnumber 
ASCII_OUT_FILENAME_LATE_HARVEST     = "harvest_late_{0}_trno{1}.asc" # mGroup_treatmentnumber 
ASCII_OUT_FILENAME_MAT_IS_HARVEST   = "harvest_before_maturity_{0}_trno{1}.asc" # mGroup_treatmentnumber 

CLIMATE_FILE_PATTERN="{0}_v3test.csv"
USER = "local" 
CROPNAME = "soybean"
NONEVALUE = -9999

SHOW_PROGRESS_BAR = True

def calculateGrid() :
    "main"

    pathId = USER
    showBar = SHOW_PROGRESS_BAR
    sourceFolder = ""
    outputFolder = ""
    if len(sys.argv) > 1 and __name__ == "__main__":
        for arg in sys.argv[1:]:
            k, v = arg.split("=")
            if k == "path":
                pathId = v
            if k == "source" :
                sourceFolder = v
            if k == "out" :
                outputFolder = v
            if k == "noprogess" :
                showBar = False
    if not sourceFolder :
        sourceFolder = PATHS[pathId]["sourcepath"]
    if not outputFolder :
        outputFolder = PATHS[pathId]["outputpath"]

    climateFolder = PATHS[pathId]["climate-data"]
    asciiOutFolder = os.path.join(outputFolder, PATHS[pathId]["ascii-out"])
    pngFolder = os.path.join(outputFolder, PATHS[pathId]["png-out"])
    pdfFolder = os.path.join(outputFolder,PATHS[pathId]["pdf-out"])
    projectpath = os.path.join(outputFolder,PATHS[pathId]["projectdatapath"])
    gridSource = os.path.join(projectpath, "stu_eu_layer_grid.csv")
    refSource = os.path.join(projectpath, "stu_eu_layer_ref.csv")

    #errorFile = os.path.join(asciiOutFolder, "error.txt") # debug output
    res = GetGridLookup(gridSource)
    extRow = res[0]
    extCol = res[1]
    gridSourceLookup = res[2] # dict() [ref] = [(row, col), ...]

    climateRef = GetClimateReference(refSource)
    
    filelist = os.listdir(sourceFolder)
    maxRef = len(filelist) + 1

    # get grid extension
    #res = fileByGrid(filelist, (3,4))
    #idxFileDic = res[2]
    #extRow = res[0]
    #extCol = res[1]

    maxAllAvgYield = 0
    maxSdtDeviation = 0
    numInput = len(filelist)
    currentInput = 0
    allGrids = dict()
    StdDevAvgGrids = dict()
    matureGrid = dict()
    flowerGrid = dict()
    harvestGrid = dict()
    matIsHavestGrid = dict()
    lateHarvestGrid = dict()
    climateFilePeriod = dict()
    coolWeatherImpactGrid = dict()
    coolWeatherDeathGrid = dict()
    coolWeatherImpactWeightGrid = dict()
    wetHarvestGrid = dict()
    sumMaxOccurrence = 0
    sumMaxDeathOccurrence = 0
    maxLateHarvest = 0
    maxWetHarvest = 0
    maxMatHarvest = 0
    sumLowOccurrence = 0
    sumMediumOccurrence = 0
    sumHighOccurrence = 0
    outputGridsGenerated = False
    # iterate over all model run results
    for sourcefileName in filelist:
        # open grid cell file
        with open(os.path.join(sourceFolder, sourcefileName)) as sourcefile:
            #EU_SOY_MO_" + soil_ref + ".csv"
            refID = int(sourcefileName.split(".")[0].split("_")[3])
            simulations = dict()
            simDoyFlower = dict()
            simDoyMature = dict()
            simDoyHarvest = dict()
            simMatIsHarvest = dict()
            simLastHarvestDate = dict()
            dateYearOrder = dict()
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
                    if IsCrop(lineContent, CROPNAME) and (lineContent[0] == "T1" or lineContent[0] == "T2") :
                        lineKey = (lineContent[:-8])
                        yieldValue = lineContent[-1]
                        period = lineContent[-8]
                        yearValue = lineContent[-7]
                        #sowValue = lineContent[-6]
                        #emergeValue = lineContent[-5]
                        flowerValue = lineContent[-4]
                        matureValue = lineContent[-3]
                        harvestValue = lineContent[-2]
                        if not lineKey in simulations :
                            simulations[lineKey] = list() 
                            simDoyFlower[lineKey] = list()
                            simDoyMature[lineKey] = list() 
                            simDoyHarvest[lineKey] = list() 
                            simMatIsHarvest[lineKey] = list() 
                            simLastHarvestDate[lineKey] = list() 
                            dateYearOrder[lineKey] = list()
                        if not lineKey[1] in climateFilePeriod :
                            climateFilePeriod[lineKey[1]] = period
                        simulations[lineKey].append(yieldValue)
                        simDoyFlower[lineKey].append(flowerValue)
                        simDoyMature[lineKey].append(matureValue if matureValue > 0 else harvestValue)
                        simDoyHarvest[lineKey].append(harvestValue)
                        simMatIsHarvest[lineKey].append(matureValue <= 0 and harvestValue > 0)
                        simLastHarvestDate[lineKey].append(datetime.fromisoformat(str(yearValue)+"-10-31").timetuple().tm_yday == harvestValue)
                        dateYearOrder[lineKey].append(yearValue)
            if not outputGridsGenerated :
                outputGridsGenerated = True
                for simKey in simulations :
                    allGrids[simKey] =  newGridLookup(maxRef, NONEVALUE)
                    StdDevAvgGrids[simKey] =  newGridLookup(maxRef, NONEVALUE)
                    matureGrid[simKey] = newGridLookup(maxRef, NONEVALUE)
                    flowerGrid[simKey] = newGridLookup(maxRef, NONEVALUE)
                    harvestGrid[simKey] = newGridLookup(maxRef, NONEVALUE)
                    matIsHavestGrid[simKey] = newGridLookup(maxRef, NONEVALUE)
                    lateHarvestGrid[simKey] = newGridLookup(maxRef, NONEVALUE)
                    coolWeatherImpactGrid[simKey] = newGridLookup(maxRef, NONEVALUE)
                    coolWeatherDeathGrid[simKey] = newGridLookup(maxRef, NONEVALUE)
                    coolWeatherImpactWeightGrid[simKey] = newGridLookup(maxRef, NONEVALUE)
                    wetHarvestGrid[simKey] = newGridLookup(maxRef, NONEVALUE)

            for simKey in simulations :
                pixelValue = CalculatePixel(simulations[simKey])
                if pixelValue > maxAllAvgYield :
                    maxAllAvgYield = pixelValue

                stdDeviation = statistics.stdev(simulations[simKey])
                if stdDeviation > maxSdtDeviation :
                    maxSdtDeviation = stdDeviation

                
                matureGrid[simKey][refID] = int(average(simDoyMature[simKey]))
                flowerGrid[simKey][refID] = int(average(simDoyFlower[simKey]))
                harvestGrid[simKey][refID] = int(average(simDoyHarvest[simKey]))
                matIsHavestGrid[simKey][refID] = int(sum(simMatIsHarvest[simKey]))
                lateHarvestGrid[simKey][refID] = int(sum(simLastHarvestDate[simKey]))
                allGrids[simKey][refID] = int(pixelValue)
                StdDevAvgGrids[simKey][refID] = int(stdDeviation)
                if maxLateHarvest < lateHarvestGrid[simKey][refID] :
                    maxLateHarvest = lateHarvestGrid[simKey][refID]
                if maxMatHarvest < matIsHavestGrid[simKey][refID] :
                    maxMatHarvest = matIsHavestGrid[simKey][refID]     

            #coolWeatherImpactGrid
            for scenario in climateFilePeriod :
                climate_row_col = climateRef[refID]
                climatePath = os.path.join(climateFolder, climateFilePeriod[scenario], scenario, CLIMATE_FILE_PATTERN.format(climate_row_col))
                if os.path.exists(climatePath) :
                    with open(climatePath) as climatefile:
                        firstLines = 0
                        numOccurrenceHigh = dict()
                        numOccurrenceMedium = dict()
                        numOccurrenceLow = dict()
                        numWetHarvest = dict()
                        header = list()
                        precipPrevDays = collections.deque(maxlen=5)
                        for line in climatefile:
                            if firstLines < 2 :
                                # read header
                                if firstLines < 1 :
                                    header = ReadClimateHeader(line)
                                firstLines += 1
                            else :
                                # load relevant line content
                                lineContent = loadClimateLine(line, header)
                                date = lineContent[0]
                                tmin = lineContent[1]
                                precip = lineContent[2]
                                precipPrevDays.append(precip)
                                dateYear = GetYear(date)
                                if tmin < 15 :
                                    for simKey in dateYearOrder :
                                        if simKey[1] == scenario :
                                            try :
                                                # get index of current year
                                                yearIndex = dateYearOrder[simKey].index(dateYear)
                                            except ValueError:
                                                break
                                            # get DOY for maturity and anthesis
                                            startDOY = simDoyFlower[simKey][yearIndex]
                                            endDOY = simDoyMature[simKey][yearIndex]
                                            if IsDateInGrowSeason(startDOY, endDOY, date):
                                                if not simKey in numOccurrenceHigh:
                                                    numOccurrenceHigh[simKey] = 0
                                                    numOccurrenceMedium[simKey] = 0
                                                    numOccurrenceLow[simKey] = 0
                                                if tmin < 8 :
                                                    numOccurrenceHigh[simKey] += 1
                                                elif tmin < 10 :
                                                    numOccurrenceMedium[simKey] += 1
                                                else :
                                                    numOccurrenceLow[simKey] += 1
                                            # check if this date is harvest
                                            harvestDOY = simDoyHarvest[simKey][yearIndex]
                                            if harvestDOY > 0 and IsDateInGrowSeason(harvestDOY, harvestDOY, date):
                                                wasWetHarvest = all(x > 0 for x in precipPrevDays)
                                                if not simKey in numWetHarvest:
                                                    numWetHarvest[simKey] = 0
                                                if wasWetHarvest :
                                                    numWetHarvest[simKey] += 1

                        for simKey in simulations :
                            if simKey[1] == scenario :
                                if allGrids[simKey][refID] > 0 :
                                    # cool weather occurrence
                                    if simKey in numOccurrenceMedium :
                                        sumOccurrence = numOccurrenceMedium[simKey] + numOccurrenceHigh[simKey] + numOccurrenceLow[simKey]
                                        sumDeathOccurrence = numOccurrenceMedium[simKey] * 10 + numOccurrenceHigh[simKey] * 100 + numOccurrenceLow[simKey]

                                        if sumLowOccurrence < numOccurrenceLow[simKey] :
                                            sumLowOccurrence = numOccurrenceLow[simKey]
                                        if sumMediumOccurrence < numOccurrenceMedium[simKey] :
                                            sumMediumOccurrence = numOccurrenceMedium[simKey]
                                        if sumHighOccurrence < numOccurrenceHigh[simKey] :
                                            sumHighOccurrence = numOccurrenceHigh[simKey]

                                        weight = 0

                                        if numOccurrenceHigh[simKey] <= 125 and numOccurrenceHigh[simKey] > 0: 
                                            weight = 9    
                                        elif numOccurrenceHigh[simKey] <= 500 and numOccurrenceHigh[simKey] > 0: 
                                            weight = 10    
                                        elif numOccurrenceHigh[simKey] <= 1000 and numOccurrenceHigh[simKey] > 0: 
                                            weight = 11
                                        elif numOccurrenceHigh[simKey] > 1000 and numOccurrenceHigh[simKey] > 0: 
                                            weight = 12
                                        elif numOccurrenceMedium[simKey] <= 75 and numOccurrenceMedium[simKey] > 0: 
                                            weight = 5
                                        elif numOccurrenceMedium[simKey] <= 150 and numOccurrenceMedium[simKey] > 0: 
                                            weight = 6
                                        elif numOccurrenceMedium[simKey] <= 300 and numOccurrenceMedium[simKey] > 0: 
                                            weight = 7    
                                        elif numOccurrenceMedium[simKey] > 300 and numOccurrenceMedium[simKey] > 0: 
                                            weight = 8
                                        elif numOccurrenceLow[simKey] <= 250 and numOccurrenceLow[simKey] > 0: 
                                            weight = 1
                                        elif numOccurrenceLow[simKey] <= 500 and numOccurrenceLow[simKey] > 0: 
                                            weight = 2
                                        elif numOccurrenceLow[simKey] <= 1000 and numOccurrenceLow[simKey] > 0: 
                                            weight = 3    
                                        elif numOccurrenceLow[simKey] > 1000 and numOccurrenceLow[simKey] > 0: 
                                            weight = 4

                                        coolWeatherImpactGrid[simKey][refID] = sumOccurrence
                                        coolWeatherDeathGrid[simKey][refID] = sumDeathOccurrence
                                        coolWeatherImpactWeightGrid[simKey][refID] = weight
                                        if sumMaxOccurrence < sumOccurrence :
                                            sumMaxOccurrence = sumOccurrence
                                        if sumMaxDeathOccurrence < sumDeathOccurrence :
                                            sumMaxDeathOccurrence = sumDeathOccurrence
                                    else :
                                        coolWeatherImpactGrid[simKey][refID] = 0
                                        coolWeatherDeathGrid[simKey][refID]= 0
                                    # wet harvest occurence
                                    if simKey in numWetHarvest :
                                        wetHarvestGrid[simKey][refID] = numWetHarvest[simKey]
                                        if maxWetHarvest < numWetHarvest[simKey] :
                                            maxWetHarvest = numWetHarvest[simKey]
                                    else :
                                        wetHarvestGrid[simKey][refID] = -1
                                else :
                                    coolWeatherImpactGrid[simKey][refID]= -100
                                    coolWeatherDeathGrid[simKey][refID] = -10000
                                    coolWeatherImpactWeightGrid[simKey][refID] = -1
                                    wetHarvestGrid[simKey][refID] = -1

            currentInput += 1 
            progress(showBar, currentInput, numInput, str(currentInput) + " of " + str(numInput))


    pdfList = dict()
    for simKey in allGrids :
        if not simKey[1] in pdfList : 
            pdfpath = os.path.join(pdfFolder, "scenario_{0}.pdf".format(simKey[1]))
            makeDir(pdfpath)
            pdfList[simKey[1]] = PdfPages(pdfpath)

    drawDateMaps(   gridSourceLookup,
                    matIsHavestGrid, 
                    ASCII_OUT_FILENAME_MAT_IS_HARVEST, 
                    extCol, extRow, 
                    asciiOutFolder, 
                    pngFolder, 
                    "Harvest before maturity - Scn: {0} {1} {2}", 
                    "counted occurrences in 30 years", 
                    showBar,
                    colormap='inferno',
                    factor=1,
                    maxVal=maxMatHarvest,
                    pdfList=pdfList, 
                    progressBar="Harvest before maturity  " )

    drawDateMaps(   gridSourceLookup,
                    lateHarvestGrid, 
                    ASCII_OUT_FILENAME_LATE_HARVEST, 
                    extCol, extRow, 
                    asciiOutFolder, 
                    pngFolder, 
                    "Auto Harvest 31. October - Scn: {0} {1} {2}", 
                    "counted occurrences in 30 years", 
                    showBar,
                    colormap='viridis',
                    factor=1,
                    maxVal=maxLateHarvest,
                    pdfList=pdfList, 
                    progressBar="Harvest 31. October           " )

    drawDateMaps(   gridSourceLookup,
                    wetHarvestGrid, 
                    ASCII_OUT_FILENAME_WET_HARVEST, 
                    extCol, extRow, 
                    asciiOutFolder, 
                    pngFolder, 
                    "Rain during/before harvest - Scn: {0} {1} {2}", 
                    "counted occurrences in 30 years", 
                    showBar,
                    colormap='nipy_spectral',
                    factor=1,
                    maxVal=maxWetHarvest,
                    pdfList=pdfList, 
                    progressBar="wet harvest           " )

    drawDateMaps(   gridSourceLookup,
                    coolWeatherImpactGrid, 
                    ASCII_OUT_FILENAME_COOL_WEATHER, 
                    extCol, extRow, 
                    asciiOutFolder, 
                    pngFolder, 
                    "Cool weather occurrence - Scn: {0} {1} {2}", 
                    "counted occurrences in 30 years", 
                    showBar,
                    colormap='nipy_spectral',
                    factor=1,
                    maxVal=sumMaxOccurrence,
                    pdfList=pdfList, 
                    progressBar="Cool weather            " )

    coolWeatherWeightLabels = ['0', '< 15°C', '< 10°C', '< 8°C' ]
    ticklist = [0, 3, 7, 11]
    drawDateMaps(   gridSourceLookup,
                    coolWeatherImpactWeightGrid, 
                    ASCII_OUT_FILENAME_COOL_WEATHER_WEIGHT, 
                    extCol, extRow, 
                    asciiOutFolder, 
                    pngFolder, 
                    "Cool weather weight - Scn: {0} {1} {2}", 
                    "weights for occurrences in 30 years", 
                    showBar,
                    colormap='gnuplot',
                    factor=1,
                    maxVal=12,
                    pdfList=pdfList, 
                    cbarLabel=coolWeatherWeightLabels,
                    ticklist=ticklist,
                    progressBar="Cool weather            " )
    drawDateMaps(   gridSourceLookup,
                    coolWeatherDeathGrid, 
                    ASCII_OUT_FILENAME_COOL_WEATHER_DEATH, 
                    extCol, extRow, 
                    asciiOutFolder, 
                    pngFolder, 
                    "Cool weather severity - Scn: {0} {1} {2}", 
                    "counted occurrences with severity factor", 
                    showBar,
                    colormap='nipy_spectral',
                    factor=0.0001,
                    maxVal=sumMaxDeathOccurrence,
                    pdfList=pdfList, 
                    progressBar="Cool weather death          " )

    drawDateMaps(   gridSourceLookup,
                    flowerGrid, 
                    ASCII_OUT_FILENAME_ANTHESIS_DOY, 
                    extCol, extRow, 
                    asciiOutFolder, 
                    pngFolder, 
                    "Anthesis DOY - Scn: {0} {1} {2}", 
                    "DOY", 
                    showBar,
                    colormap='viridis',
                    factor=1,
                    pdfList=pdfList, 
                    minVal=-1,
                    maxVal=306,
                    progressBar="Anthesis DOY            " )

    drawDateMaps(   gridSourceLookup,
                    matureGrid, 
                    ASCII_OUT_FILENAME_MAT_DOY, 
                    extCol, extRow, 
                    asciiOutFolder, 
                    pngFolder, 
                    "Maturity DOY - Scn: {0} {1} {2}",    
                    "DOY",               
                    showBar,                       
                    colormap='viridis',
                    factor=1,
                    minVal=-1,
                    maxVal=306,
                    pdfList=pdfList, 
                    progressBar="Maturity DOY            " )


    #write average yield grid 
    drawDateMaps(   gridSourceLookup,
                    allGrids, 
                    ASCII_OUT_FILENAME_AVG, 
                    extCol, extRow, 
                    asciiOutFolder, 
                    pngFolder, 
                    "Average Yield - Scn: {0} {1} {2}",    
                    'Yield in t',          
                    showBar,                            
                    colormap='viridis',
                    factor=1,
                    maxVal=maxAllAvgYield,
                    pdfList=pdfList, 
                    progressBar="average yield grids     " )

    drawDateMaps(   gridSourceLookup,
                    StdDevAvgGrids, 
                    ASCII_OUT_FILENAME_DEVI_AVG, 
                    extCol, extRow, 
                    asciiOutFolder, 
                    pngFolder, 
                    "Std Deviation - Scn: {0} {1} {2}",    
                    "standart deviation",    
                    showBar,                                  
                    colormap='cool',
                    factor=1,
                    minVal=0,
                    maxVal=maxSdtDeviation,
                    pdfList=pdfList, 
                    progressBar="std deviation grids          " )



    ### Start calculate max yield layer and maturity layer grid 
    maxYieldGrids = dict()
    matGroupGrids = dict()
    maxYieldDeviationGrids = dict()
    matGroupDeviationGrids = dict()
    matGroupIdGrids = dict()
    matIdcounter = 0    
    matGroupIdGrids["none"] = matIdcounter # maturity group id for 'no yield'
    # set ids for each maturity group
    for simKey in allGrids :
        if not simKey[2] in matGroupIdGrids :
            matIdcounter += 1
            matGroupIdGrids[simKey[2]] = matIdcounter

    for simKey in allGrids :
        #treatmentNoIdx, climateSenarioCIdx, mGroupCIdx, yieldsCIdx
        scenarioKey = (simKey[0], simKey[1], simKey[3])
        if not scenarioKey in maxYieldGrids :
            maxYieldGrids[scenarioKey] = newGridLookup(maxRef, NONEVALUE)
            matGroupGrids[scenarioKey] = newGridLookup(maxRef, NONEVALUE)
            maxYieldDeviationGrids[scenarioKey] = newGridLookup(maxRef, NONEVALUE)
            matGroupDeviationGrids[scenarioKey] = newGridLookup(maxRef, NONEVALUE)
        currGrid = allGrids[simKey]

        for ref in range(maxRef) :
            if currGrid[ref] > maxYieldGrids[scenarioKey][ref] :
                maxYieldGrids[scenarioKey][ref] = currGrid[ref]
                maxYieldDeviationGrids[scenarioKey][ref] = currGrid[ref]
                if currGrid[ref] == 0 :
                    matGroupGrids[scenarioKey][ref] = matGroupIdGrids["none"]
                    matGroupDeviationGrids[scenarioKey][ref] = matGroupIdGrids["none"]
                else :
                    matGroupGrids[scenarioKey][ref] = matGroupIdGrids[simKey[2]]
                    matGroupDeviationGrids[scenarioKey][ref] = matGroupIdGrids[simKey[2]]

    invMatGroupIdGrids = {v: k for k, v in matGroupIdGrids.items()}

    for simKey in allGrids :
        #treatmentNoIdx, climateSenarioIdx, mGroupIdx, CommentIdx
        scenarioKey = (simKey[0], simKey[1], simKey[3])

        currGridYield = allGrids[simKey]
        currGridDeviation = StdDevAvgGrids[simKey]
        for ref in range(maxRef) :
            if matGroupDeviationGrids[scenarioKey][ref] != NONEVALUE :
                matGroup = invMatGroupIdGrids[matGroupDeviationGrids[scenarioKey][ref]]
                matGroupKey = (simKey[0], simKey[1], matGroup, simKey[3])
                if currGridYield[ref] > maxYieldGrids[scenarioKey][ref] * 0.9 and currGridDeviation[ref] < StdDevAvgGrids[matGroupKey][ref] :
                    maxYieldDeviationGrids[scenarioKey][ref] = currGridYield[ref]
                    matGroupDeviationGrids[scenarioKey][ref] = matGroupIdGrids[simKey[2]]

    currentInput = 0
    numInput = len(maxYieldDeviationGrids)
    for simKey in maxYieldDeviationGrids :
        # ASCII_OUT_FILENAME_MAX_YIELD = "maxyield_trno{1}.asc" # treatmentnumber 
        gridFileName = ASCII_OUT_FILENAME_MAX_YIELD_DEVI.format(simKey[0])
        gridFileName = gridFileName.replace("/", "-") #remove directory seperator from filename
        gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
        # create ascii file
        file = writeAGridHeader(gridFilePath, extCol, extRow, maxValue = maxAllAvgYield)
        WriteRows(file, extRow, extCol, maxYieldDeviationGrids, simKey, gridSourceLookup)
        file.close()

        # create png
        pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
        title = "Max avg yield minus std deviation - Scn: {0} {1}".format(simKey[1], simKey[2])
        labelText = 'Yield in t'
        colormap = 'jet'
        writeMetaFile(gridFilePath, title, labelText, colormap, maxValue = maxAllAvgYield)
        createImgFromMeta(gridFilePath, gridFilePath+".meta", pngFilePath, pdf=pdfList[simKey[1]])
        #createImg(gridFilePath, pngFilePath, title, label=labelText, colormap=colormap, pdf=pdfList[simKey[1]])
        currentInput += 1 
        progress(showBar, currentInput, numInput, str(currentInput) + " of " + str(numInput) + " max yields grids      ")

    currentInput = 0
    numInput = len(maxYieldGrids)
    for simKey in maxYieldGrids :
        # ASCII_OUT_FILENAME_MAX_YIELD = "maxyield_trno{1}.asc" # treatmentnumber 
        gridFileName = ASCII_OUT_FILENAME_MAX_YIELD.format(simKey[0])
        gridFileName = gridFileName.replace("/", "-") #remove directory seperator from filename
        gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
        # create ascii file
        file = writeAGridHeader(gridFilePath, extCol, extRow, maxValue = maxAllAvgYield)
        WriteRows(file, extRow, extCol, maxYieldGrids, simKey, gridSourceLookup)
        file.close()
        # create png
        pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
        title = "Max average yield - Scn: {0} {1}".format(simKey[1], simKey[2])
        labelText='Yield in t'
        colormap='jet'
        writeMetaFile(gridFilePath, title, labelText, colormap, maxValue = maxAllAvgYield)
        createImgFromMeta(gridFilePath, gridFilePath+".meta", pngFilePath, pdf=pdfList[simKey[1]])
        #createImg(gridFilePath, pngFilePath, title, label, colormap, pdf=pdfList[simKey[1]])
        currentInput += 1 
        progress(showBar, currentInput, numInput, str(currentInput) + " of " + str(numInput) + " max yields grids      ")

    currentInput = 0
    numInput = len(matGroupGrids)
    sidebarLabel = [""] * (len(matGroupIdGrids)+1)
    colorList = ['cyan', 'lightgreen', 'magenta','crimson', 'blue','gold', 'navy']
    #cMap = ListedColormap(colorList)
    for id in matGroupIdGrids :
        sidebarLabel[matGroupIdGrids[id]] = id
    ticklist = [0] * (len(sidebarLabel))
    for tick in range(len(ticklist)) :
        ticklist[tick] = tick + 0.5
    for simKey in matGroupGrids :
        # ASCII_OUT_FILENAME_MAX_YIELD_MAT = "maxyield_matgroup_trno{1}.asc" # treatmentnumber 
        gridFileName = ASCII_OUT_FILENAME_MAX_YIELD_MAT.format(simKey[0])
        gridFileName = gridFileName.replace("/", "-") #remove directory seperator from filename
        gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
        # create ascii file
        file = writeAGridHeader(gridFilePath, extCol, extRow, minValue=0, maxValue=len(sidebarLabel)-1)
        WriteRows(file, extRow, extCol, matGroupGrids, simKey, gridSourceLookup)
        file.close()
        # create png
        pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
        title = "Maturity groups for max average yield - Scn: {0} {1}".format(simKey[1], simKey[2])
        writeMetaFile(gridFilePath, title, 'Maturity Group', colorlist=colorList, cbarLabel=sidebarLabel, ticklist=ticklist, factor=1, minValue=0, maxValue=len(sidebarLabel)-1)
        createImgFromMeta(gridFilePath, gridFilePath+".meta", pngFilePath, pdf=pdfList[simKey[1]])
        #createImg(gridFilePath, pngFilePath, title, label='Maturity Group', colormap=cMap, factor=1, cbarLabel=sidebarLabel, ticklist=ticklist, pdf=pdfList[simKey[1]])
        currentInput += 1 
        progress(showBar, currentInput, numInput, str(currentInput) + " of " + str(numInput) + " mat groups grids          ")

    currentInput = 0
    numInput = len(matGroupDeviationGrids)
    for simKey in matGroupDeviationGrids :
        gridFileName = ASCII_OUT_FILENAME_MAX_YIELD_MAT_DEVI.format(simKey[0])
        gridFileName = gridFileName.replace("/", "-") #remove directory seperator from filename
        gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
        # create ascii file
        file = writeAGridHeader(gridFilePath, extCol, extRow, minValue=0, maxValue=len(sidebarLabel)-1)
        WriteRows(file, extRow, extCol, matGroupDeviationGrids, simKey, gridSourceLookup)
        file.close()
        # create png
        pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
        title = "Maturity groups - max avg yield minus deviation  - Scn: {0} {1}".format(simKey[1], simKey[2])
        writeMetaFile(gridFilePath, title, 'Maturity Group', colorlist=colorList, cbarLabel=sidebarLabel, ticklist=ticklist, factor=1, minValue=0, maxValue=len(sidebarLabel)-1)
        createImgFromMeta(gridFilePath, gridFilePath+".meta", pngFilePath, pdf=pdfList[simKey[1]])
        #createImg(gridFilePath, pngFilePath, title, label='Maturity Group', colormap=cMap, factor=1, cbarLabel=sidebarLabel, ticklist=ticklist, pdf=pdfList[simKey[1]])
        currentInput += 1 
        progress(showBar, currentInput, numInput, str(currentInput) + " of " + str(numInput) + " mat groups grids          ")

    #### END calculate max yield layer and maturity layer grid 


    #### Grid Diff affected by water stress T4(potential) - T1(actual) 
    currentInput = 0
    numInput = len(allGrids)
    for simKey in allGrids :
        # treatment number
        if simKey[0] == "T1" :
            otherKey = ("T2",simKey[1], simKey[2], "Unlimited water")
            newDiffGrid = GridDifference(allGrids[otherKey], allGrids[simKey], maxRef)
            
            gridFileName = ASCII_OUT_FILENAME_WATER_DIFF.format(simKey[2])
            gridFileName = gridFileName.replace("/", "-") #remove directory seperator from filename
            gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
            # create ascii file
            file = writeAGridHeader(gridFilePath, extCol, extRow, maxValue=maxAllAvgYield)
            
            for row in range(extRow) :
                line = ""
                for col in range(extCol) :
                    line += str(newDiffGrid[gridSourceLookup[row][col] ]) + " "
                file.write(line + "\n")
            file.close()
            # create png
            pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
            title = "Water stress effect on potential yield - Scn: {0} {1}".format(simKey[1], simKey[2])
            labelText='Difference yield in t'
            colormap='Wistia'
            writeMetaFile(gridFilePath, title, labelText, colormap, maxValue=maxAllAvgYield)
            createImgFromMeta(gridFilePath, gridFilePath+".meta", pngFilePath, pdf=pdfList[simKey[1]])
            #createImg(gridFilePath, pngFilePath, title, label, colormap, pdf=pdfList[simKey[1]])
            currentInput += 1 
            progress(showBar, currentInput, numInput, str(currentInput) + " of " + str(numInput) + " water diff grids         ")

    currentInput = 0
    numInput = len(maxYieldGrids)
    for simKey in maxYieldGrids :
        # treatment number
        if simKey[0] == "T1" :
            otherKey = ("T2",simKey[1], "Unlimited water")
            newDiffGrid = GridDifference(maxYieldGrids[otherKey], maxYieldGrids[simKey], maxRef)
            
            gridFileName = ASCII_OUT_FILENAME_WATER_DIFF_MAX
            gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
            # create ascii file
            file = writeAGridHeader(gridFilePath, extCol, extRow, maxValue=maxAllAvgYield)
            for row in range(extRow) :
                line = ""
                for col in range(extCol) :
                    line += str(newDiffGrid[gridSourceLookup[row][col] ]) + " "
                file.write(line + "\n")
            file.close()
            # create png
            pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
            title = "Water stress effect on potential max yield - Scn: {0}".format(simKey[1])
            labelText='Difference yield in t'
            colormap='Wistia'
            writeMetaFile(gridFilePath, title, labelText, colormap, maxValue=maxAllAvgYield)
            createImgFromMeta(gridFilePath, gridFilePath+".meta", pngFilePath, pdf=pdfList[simKey[1]])
            #createImg(gridFilePath, pngFilePath, title, label, colormap, pdf=pdfList[simKey[1]])
            currentInput += 1 
            progress(showBar, currentInput, numInput, str(currentInput) + " of " + str(numInput) + " water diff grids max      ")

    for simKey in pdfList :
        pdfList[simKey].close()

    print("\n\n")
    print("Low:", sumLowOccurrence )
    print("Medium:", sumMediumOccurrence )
    print("High:", sumHighOccurrence )


def newGrid(extRow, extCol, defaultVal) :
    grid = [defaultVal] * extRow
    for i in range(extRow) :
        grid[i] = [defaultVal] * extCol
    return grid

def newGridLookup(maxRef, defaultVal) :
    grid = [defaultVal] * maxRef
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
    if counter > 3 :
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
        if token == "EmergDOY" : 
            emergDOYIdx = i
        if token == "SowDOY" : 
            sowDOYIdx = i
        if token == "AntDOY" : 
            antDOYIdx = i
        if token == "MatDOY" : 
            matDOYIdx = i
        if token == "HarvDOY" : 
            harvDOYIdx = i
        if token == "Year" : 
            yearIdx = i
        if token == "period" : 
            periodIdx = i

    return (treatNoIdx, climateSenarioCIdx, mGroupCIdx, commentIdx, periodIdx, yearIdx, sowDOYIdx, emergDOYIdx, antDOYIdx, matDOYIdx, harvDOYIdx, yieldsCIdx)

def IsCrop(key, cropName) :
    return key[2].startswith(cropName) 

def GetYear(dateStr) :
    return datetime.fromisoformat(dateStr).timetuple().tm_year

def IsDateInGrowSeason(startDOY, endDOY, dateStr) :
    date = datetime.fromisoformat(dateStr)
    doy = date.timetuple().tm_yday
    if doy >= startDOY and doy <= endDOY :
        return True
    return False


def loadLine(line, header) :
    # read relevant content from line 
    tokens = line.split(",")
    treatNo = tokens[header[0]] # some ID
    climateSenario = tokens[header[1]] # some ID
    mGroup = tokens[header[2]] # some ID
    comment = tokens[header[3]]
    period = tokens[header[4]]
    year = int(tokens[header[5]])
    sowDOY = validDOY(tokens[header[6]])
    emergDOY = validDOY(tokens[header[7]])
    antDOY = validDOY(tokens[header[8]])
    matDOY = validDOY(tokens[header[9]])
    harDOY = validDOY(tokens[header[10]])
    yields = float(tokens[header[11]])
    return (treatNo, climateSenario, mGroup, comment, period, year, sowDOY, emergDOY, antDOY, matDOY, harDOY, yields)

def GridDifference(grid1, grid2, maxRef) :
    # calculate the difference between 2 grids, save it to new grid
    newGridDiff = newGridLookup(maxRef, NONEVALUE) 
    for ref in range(maxRef) :
        if  grid1[ref] != NONEVALUE and grid2[ref] != NONEVALUE: 
            newGridDiff[ref] = grid1[ref] - grid2[ref]
        else :
            newGridDiff[ref] = NONEVALUE
    return newGridDiff

def validDOY(s):
    # return a valid DOY or -1 from string 
    try: 
        value = int(s)
        return value
    except ValueError:
        return -1

def GetGridfromFilename(filename, tokenPositions) :
    # get row and colum from a filename, by given token positions, split by '_'
    basename = os.path.basename(filename)
    rol_col_tuple = (-1,-1)
    if basename.endswith(".csv") :
        basename = basename[:-4]
        tokens = basename.split("_") 
        row = int(tokens[tokenPositions[0]])
        col = int(tokens[tokenPositions[1]])
        rol_col_tuple = (row,col)

    return rol_col_tuple


def writeAGridHeader(name, nCol, nRow, cornerX=0.0, cornery=0.0, novalue=-9999, cellsize=1.0, maxValue=-9999, minValue=-9999) :
    # create an ascii file, which contains the header 
    makeDir(name)
    file=open(name,"w")
    file.write("ncols {0}\n".format(nCol))
    file.write("nrows {0}\n".format(nRow))
    file.write("xllcorner     {0}\n".format(cornerX))
    file.write("yllcorner     {0}\n".format(cornery))
    file.write("cellsize      {0}\n".format(cellsize))
    file.write("NODATA_value  {0}\n".format(novalue))

    # file.write("{0} {1}".format(maxValue, minValue))
    # for _ in range(2,nCol) :
    #     file.write(" {0}".format(novalue))
    # file.write("\n")
    return file

def average(list) :
    val = 0.0
    lenVal = 0
    for x in list :
        if x >= 0 :
            val += x 
            lenVal +=1
    if lenVal > 0 :               
        val = val / lenVal 
        #val = sum(list) / len(list) 
    return val

def fileByGrid(filelist, tokenPositions) :
    extCol = 0
    extRow = 0
    idxFileDic = dict()
    for filename in filelist: 
        grid = GetGridfromFilename(filename, tokenPositions)
        if grid[0] == -1 :
            continue
        else : 
            if extRow < grid[0] :
                extRow = grid[0]
            if extCol < grid[1] :
                extCol = grid[1]

        #indexed file list by grid, remove all none csv        
        idxFileDic[grid] = filename
    return (extRow, extCol, idxFileDic)

def GetGridLookup(gridsource) :
    colExt = 0
    rowExt = 0
    lookup = dict()
    with open(gridsource) as sourcefile:
        firstLine = True
        colID = -1
        rowID = -1
        refID = -1
        for line in sourcefile:
            tokens = line.strip().split(",")          
            if firstLine :
                # read header
                firstLine = False
                for index in range(len(tokens)) :
                    token = tokens[index]
                    if token == "Column_":
                        colID = index
                    if token == "Row":
                        rowID= index
                    if token == "soil_ref" :
                        refID = index
            else :
                col = int(tokens[colID])
                row = int(tokens[rowID])
                ref = int(tokens[refID])
                if int(tokens[colID]) > colExt :
                    colExt = int(tokens[colID])
                if int(tokens[rowID]) > rowExt :
                    rowExt = int(tokens[rowID])
                if  not ref in lookup :
                    lookup[ref] = list()
                lookup[ref].append((row, col))

    lookupGrid = newGrid(rowExt, colExt, NONEVALUE)
    for ref in lookup :
        for row, col in lookup[ref] :
            lookupGrid[row-1][col-1] = ref

    return (rowExt, colExt, lookupGrid)

def GetClimateReference(refSource) :
    lookup = dict()
    with open(refSource) as sourcefile:
        firstLine = True
        refID = -1
        climateID = -1
        for line in sourcefile:
            tokens = line.strip().split(",")            
            if firstLine :
                # read header
                firstLine = False
                for index in range(len(tokens)) :
                    token = tokens[index]
                    if token == "CLocation":
                        climateID= index
                    if token == "soil_ref" :
                        refID = index
            else :
                climate = tokens[climateID]
                ref = int(tokens[refID])
                lookup[ref] = climate
    return lookup

def ReadClimateHeader(line) : 
    #read header
    tokens = line.split(",")
    i = -1
    for token in tokens :
        i = i+1
        if token == "iso-date":
            dateIdx = i
        if token == "tmin":
            tminIdx = i
        if token == "precip":
            precipIdx = i

    return (dateIdx, tminIdx, precipIdx)


def loadClimateLine(line, header) :
    tokens = line.split(",")
    date = tokens[header[0]] 
    tmin = float(tokens[header[1]]) 
    precip = float(tokens[header[2]]) 
    return (date, tmin, precip)


def drawDateMaps(gridSourceLookup, grids, filenameFormat, extCol, extRow, asciiOutFolder, pngFolder, titleFormat, labelText, showBar, colormap='viridis', cbarLabel=None, ticklist=None, factor=0.001, maxVal=-9999, minVal=-9999, pdfList=None, progressBar="           " ) :
    currentInput = 0
    numInput = len(grids)
    for simKey in grids :
        #simkey = treatmentNo, climateSenario, maturityGroup, comment
        gridFileName = filenameFormat.format(simKey[2], simKey[0])
        gridFileName = gridFileName.replace("/", "-") #remove directory seperator from filename
        gridFilePath = os.path.join(asciiOutFolder, simKey[1], gridFileName)
        file = writeAGridHeader(gridFilePath, extCol, extRow, maxValue=maxVal, minValue=minVal)

        WriteRows(file, extRow, extCol, grids, simKey, gridSourceLookup)
        file.close()
        # create png
        pngFilePath = os.path.join(pngFolder, simKey[1], gridFileName[:-3]+"png")
        title = titleFormat.format(simKey[1], simKey[2], simKey[3])
        writeMetaFile(gridFilePath, title, labelText, colormap=colormap, cbarLabel=cbarLabel, ticklist=ticklist, factor=factor, maxValue=maxVal, minValue=minVal)

        pdfFile = None
        if pdfList :
            pdfFile = pdfList[simKey[1]]
        createImgFromMeta(gridFilePath, gridFilePath+".meta", pngFilePath, pdf=pdfFile) 
        #createImg(gridFilePath, pngFilePath, title, colormap=colormap, cbarLabel=cbarLabel, ticklist=ticklist, factor=factor, label=labelText, pdf=pdfFile)
        currentInput += 1 
        progress(showBar, currentInput, numInput, str(currentInput) + " of " + str(numInput) + " " + progressBar)

def WriteRows(file, extRow, extCol, grids, simKey, gridSourceLookup) :
    simGrid = grids[simKey]
    for row in range(extRow) :
        line = ""
        for col in range(extCol) :
            refID = gridSourceLookup[row][col]
            if refID >= 0 :
                line += str(simGrid[refID]) + " "
            else : 
               line += "-9999 " 
        file.write(line + "\n")


def writeMetaFile(gridFilePath, title, labeltext, colormap='', colorlist=None, cbarLabel=None, ticklist=None, factor=0.001,  maxValue=-9999, minValue=-9999):
    metaFilePath = gridFilePath+".meta"
    makeDir(metaFilePath)
    file=open(metaFilePath,"w")
    file.write("title: '{0}'\n".format(title))
    file.write("labeltext: '{0}'\n".format(labeltext))
    if colormap :
        file.write("colormap: '{0}'\n".format(colormap))
    if colorlist :
        file.write("colorlist: \n")        
        for item in colorlist :
            file.write(" - '{0}'\n".format(item))
    if cbarLabel :
        file.write("cbarLabel: \n")        
        for cbarItem in cbarLabel :
            file.write(" - '{0}'\n".format(cbarItem))
    if cbarLabel :
        file.write("ticklist: \n")        
        for tick in ticklist :
            file.write(" - {0}\n".format(tick))
    file.write("factor: {0}\n".format(factor))
    if not maxValue == NONEVALUE :
        file.write("maxValue: {0}\n".format(maxValue))
    if not minValue == NONEVALUE :
        file.write("minValue: {0}\n".format(minValue))
    file.close()

def progress(showBar, count, total, status=''):
    # draw a progress bar in cmd line
    if showBar :
        bar_len = 60
        filled_len = int(round(bar_len * count / float(total)))

        percents = round(100.0 * count / float(total), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)

        sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
        sys.stdout.flush()

def WriteError(filename, errorMsg) :
    # debug write to text file
    f=open(filename, "a+")
    f.write("Error: " + errorMsg + "\r\n")
    f.close()

def createImg(ascii_path, out_path, title, label='Yield in t', colormap='viridis', factor=0.001, cbarLabel=None, ticklist=None, pdf=None) :
    # Read in ascii header data
    with open(ascii_path, 'r') as source:
        ascii_header = source.readlines()[:6]
    
    # Read the ASCII raster header
    ascii_header = [item.strip().split()[-1] for item in ascii_header]
    ascci_cols = int(ascii_header[0])
    ascii_rows = int(ascii_header[1])
    ascii_xll = float(ascii_header[2])
    ascii_yll = float(ascii_header[3])
    ascii_cs = float(ascii_header[4])
    ascii_nodata = float(ascii_header[5])
    
    # Read in the ascii data array
    ascii_data_array = np.loadtxt(ascii_path, dtype=np.float, skiprows=6)
    
    # Set the nodata values to nan
    ascii_data_array[ascii_data_array == ascii_nodata] = np.nan
    
    # data is stored as an integer but scaled by a factor
    ascii_data_array *= factor

    image_extent = [
        ascii_xll, ascii_xll + ascci_cols * ascii_cs,
        ascii_yll, ascii_yll + ascii_rows * ascii_cs]
    
    # Plot data array
    fig, ax = plt.subplots()
    ax.set_title(title)
    
    # Get the img object in order to pass it to the colorbar function
    img_plot = ax.imshow(ascii_data_array, cmap=colormap, extent=image_extent)

    if ticklist :
        # Place a colorbar next to the map
        cbar = plt.colorbar(img_plot, ticks=ticklist, orientation='vertical', shrink=0.5, aspect=14)
    else :
        # Place a colorbar next to the map
        cbar = plt.colorbar(img_plot, orientation='vertical', shrink=0.5, aspect=14)
    cbar.set_label(label)
    if cbarLabel :
        cbar.ax.set_yticklabels(cbarLabel) 

    ax.grid(True, alpha=0.5)
    # save image and pdf 
    makeDir(out_path)
    if pdf :
        pdf.savefig(dpi=150)
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    

def createImgFromMeta(ascii_path, meta_path, out_path, pdf=None) :

    # Read in ascii header data
    with open(ascii_path, 'r') as source:
        ascii_header = source.readlines()[:6]

    # Read the ASCII raster header
    ascii_header = [item.strip().split()[-1] for item in ascii_header]
    ascci_cols = int(ascii_header[0])
    ascii_rows = int(ascii_header[1])
    ascii_xll = float(ascii_header[2])
    ascii_yll = float(ascii_header[3])
    ascii_cs = float(ascii_header[4])
    ascii_nodata = float(ascii_header[5])
    
    title="" 
    label=""
    colormap = 'viridis'
    cMap = None
    cbarLabel = None
    factor = 0.001
    ticklist = None
    maxValue = ascii_nodata
    maxLoaded = False
    minValue = ascii_nodata
    minLoaded = False

    with open(meta_path, 'rt') as meta:
       # documents = yaml.load(meta, Loader=yaml.FullLoader)
        yaml=YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
        documents = yaml.load(meta)
        #documents = yaml.full_load(meta)

        for item, doc in documents.items():
            print(item, ":", doc)
            if item == "title" :
                title = doc
            elif item == "labeltext" :
                label = doc
            elif item == "factor" :
                factor = float(doc)
            elif item == "maxValue" :
                maxValue = float(doc)
                maxLoaded = True
            elif item == "minValue" :
                minValue = float(doc)
                minLoaded = True
            elif item == "colormap" :
                colormap = doc
            elif item == "colorlist" :
                cMap = doc
            elif item == "cbarLabel" :
                cbarLabel = doc
            elif item == "ticklist" :
                ticklist = list()
                for i in doc :
                    ticklist.append(float(i))


    # Read in the ascii data array
    ascii_data_array = np.loadtxt(ascii_path, dtype=np.float, skiprows=6)
    
    # Set the nodata values to nan
    ascii_data_array[ascii_data_array == ascii_nodata] = np.nan

    # data is stored as an integer but scaled by a factor
    ascii_data_array *= factor
    maxValue *= factor
    minValue *= factor

    image_extent = [
        ascii_xll, ascii_xll + ascci_cols * ascii_cs,
        ascii_yll, ascii_yll + ascii_rows * ascii_cs]
    
    # Plot data array
    fig, ax = plt.subplots()
    ax.set_title(title)
    
    # Get the img object in order to pass it to the colorbar function
    if cMap :
        colorM = ListedColormap(cMap)
        if minLoaded and maxLoaded:
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmin=minValue, vmax=maxValue)
        elif minLoaded :
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmax=minValue)
        elif maxLoaded :
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none', vmax=maxValue)
        else :
            img_plot = ax.imshow(ascii_data_array, cmap=colorM, extent=image_extent, interpolation='none')
    else :
        if minLoaded and maxLoaded:
            img_plot = ax.imshow(ascii_data_array, cmap=colormap, extent=image_extent, interpolation='none', vmin=minValue, vmax=maxValue)
        elif minLoaded :
            img_plot = ax.imshow(ascii_data_array, cmap=colormap, extent=image_extent, interpolation='none', vmax=minValue)
        elif maxLoaded :
            img_plot = ax.imshow(ascii_data_array, cmap=colormap, extent=image_extent, interpolation='none', vmax=maxValue)
        else :
            img_plot = ax.imshow(ascii_data_array, cmap=colormap, extent=image_extent, interpolation='none')

    if ticklist :
        # Place a colorbar next to the map
        cbar = plt.colorbar(img_plot, ticks=ticklist, orientation='vertical', shrink=0.5, aspect=14)
    else :
        # Place a colorbar next to the map
        cbar = plt.colorbar(img_plot, orientation='vertical', shrink=0.5, aspect=14)
    cbar.set_label(label)
    if cbarLabel :
        cbar.ax.set_yticklabels(cbarLabel) 

    ax.grid(True, alpha=0.5)
    # save image and pdf 
    makeDir(out_path)
    if pdf :
        pdf.savefig(dpi=150)
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
import os    
import sys
import math
import statistics 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.backends.backend_pdf import PdfPages
import errno

NONEVALUE=-9999

outFile = os.path.join("./", "out_frost.csv")
outASCIItemp = os.path.join("./", "out_temp.asc")
outASCIIocc = os.path.join("./", "out_occ.asc")
outbinary= os.path.join("./", "out_bin.asc")

def calculateGrid() :

    if os.path.exists(outFile):
        os.remove(outFile)

    inputFolder = "C:/Users/sschulz/Desktop/soybean/climate-data/transformed/0/0_0"
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
    outputFilesGenerated = False
    numFiles = len(idxFileDic)
    current = 1
    # iterate over all grid cells 
    for currRow in range(1, extRow+1) :
        for currCol in range(1, extCol+1) :
            gridIndex = (currRow, currCol)
            if gridIndex in idxFileDic : 
                with open(os.path.join(inputFolder, idxFileDic[gridIndex])) as sourcefile:
                    firstLines = 0
                    numOccurence = 0
                    minValue = 10.0
                    header = list()
                    for line in sourcefile:
                        if firstLines < 2 :
                            # read header
                            if firstLines < 1 :
                                header = ReadHeader(line)
                            firstLines += 1
                        else :
                            # load relevant line content
                            lineContent = loadLine(line, header)
                            date = lineContent[0]
                            tmin = lineContent[1]
                            # check for the lines with a specific crop
                            if IsDateInGrowSeason(5, 8, date) and tmin < 0:
                                numOccurence += 1
                                if tmin < minValue :
                                    minValue = tmin 
                    
                    if numOccurence > 0 and minValue < 0:
                        WriteError(outFile, "{0},{1},{2},{3}".format(currRow, currCol, numOccurence, minValue)) 
                    if not outputFilesGenerated :
                        outputFilesGenerated = True
                        lowTempGrid =  newGrid(extRow, extCol, NONEVALUE)
                        occurenceGrid =  newGrid(extRow, extCol, NONEVALUE)
                        binaryOcc = newGrid(extRow, extCol, NONEVALUE)

                    lowTempGrid[currRow-1][currCol-1] = int(minValue)
                    occurenceGrid[currRow-1][currCol-1] = int(numOccurence)
                    binaryOcc[currRow-1][currCol-1] = 0 
                    if numOccurence == 1 :
                         binaryOcc[currRow-1][currCol-1] = 1
                    if numOccurence == 2 :
                         binaryOcc[currRow-1][currCol-1] = 2
                    if numOccurence == 3 :
                         binaryOcc[currRow-1][currCol-1] = 3
                    if numOccurence > 3 :
                        binaryOcc[currRow-1][currCol-1] = 4

                progress(current, numFiles, status='processing climate Files')
                current += 1 
    writeGrid(extCol, extRow, lowTempGrid, outASCIItemp, "Temperature < 0 May - August", "Temperature < 0 °C")
    writeGrid(extCol, extRow, occurenceGrid, outASCIIocc, "Temperature < 0 incidents, May - August", "incidents over 1980-2010")
    #cMap = ListedColormap(["yellow", "green", "darkcyan", "navy"])
    labelSteps= ["0", "1", "2", "3", ">3" ]
    writeGrid(extCol, extRow, binaryOcc, outbinary, "Temperature < 0 incidents, May - August", "grouped incidents 1980-2010", labelSteps=labelSteps)

def redoImages() :
    
    createImg(  outASCIItemp, 
                outASCIItemp[:-3]+"png", 
                "Temperature < 0 May - August", 
                label="counted",
                factor=1)

    createImg(  outASCIIocc, 
                outASCIIocc[:-3]+"png", 
                "Temperature < 0 incidents, May - August", 
                label="Temperature in °C",
                factor=1)

    cMap = ListedColormap(["yellow", "green", "darkcyan", "navy"])
    labelSteps= ["0", "1-2", "3-29", ">30"]
    createImg(  outbinary, 
                outbinary[:-3]+"png", 
                "Temperature < 0 incidents, May - August", 
                label="counted",
                factor=1, 
                colormap='viridis',
                cbarLabel=labelSteps)


def newGrid(extRow, extCol, defaultVal) :
    grid = [defaultVal] * extRow
    for i in range(extRow) :
        grid[i] = [defaultVal] * extCol
    return grid

def writeGrid(extCol, extRow, grid, filename, title, labeltext, colormap='viridis', labelSteps=None) :
    file = writeAGridHeader(filename, extCol, extRow)
    for row in range(extRow-1, -1, -1) :
        seperator = ' '
        file.write(seperator.join(map(str, grid[row])) + "\n")
    file.close()
    # create png
    pngFilePath = filename[:-3]+"png"
    createImg(filename, pngFilePath, title, factor=1, label=labeltext, colormap=colormap, cbarLabel=labelSteps)

def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

def WriteError(filename, errorMsg) :
    f=open(filename, "a+", newline="")
    f.write(errorMsg + "\r\n")
    f.close()

def IsDateInGrowSeason(start, end, date) :
    tokens = date.split("-")

    month = int(tokens[1]) # month
    if month >= start and month <= end :
        return True
    return False

def ReadHeader(line) : 
    #read header
    tokens = line.split(",")
    i = -1
    for token in tokens :
        i = i+1
        if token == "iso-date":
            dateIdx = i
        if token == "tmin":
            tminIdx = i

    return (dateIdx, tminIdx)


def loadLine(line, header) :
    tokens = line.split(",")
    date = tokens[header[0]] 
    tmin = float(tokens[header[1]]) 
    return (date, tmin)


def GetGridfromFilename(filename) :
    basename = os.path.basename(filename)
    rol_col_tuple = (-1,-1)
    if basename.endswith(".csv") :
        tokens = basename.split("_") 
        if len(tokens) > 2 :
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
    file.write("\n")
    return file

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
        # tick = 0.5 - len(cbarLabel) / 100 
        tickslist = [0] * len(cbarLabel)
        for i in range(len(cbarLabel)) :
            tickslist[i] += i 

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
    #redoImages()
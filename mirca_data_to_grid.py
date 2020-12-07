#!/usr/bin/python
# -*- coding: UTF-8

import gzip
from dataclasses import dataclass
import os
import numpy as np

def build() :
    "main"

    gridFile = "./stu_eu_layer_grid.csv"
    pathToSoyIrrGrids = "./irrGrids"
    outFile = "./stu_eu_layer_grid_irrigation.csv"

    # read all 12 month data
    # join them into one data set
    # create a lat/lon map, assigning each Datapoint a lat/lon value
    # interpolate for each stu_eu grid point the matching data point
    final_arr = list()
    for root, dirs, files in os.walk(pathToSoyIrrGrids):
        if len(files) > 0 :
            print("root", root)
            print("dirs", dirs)
        for file in files:
            print("File:", file)
            header = readAsciiHeader(os.path.join(root, file))
            ascii_data_array = np.loadtxt(header.ascii_path, dtype=np.float, skiprows=6)
            # Set the nodata values to nan
            ascii_data_array[ascii_data_array == header.ascii_nodata] = np.nan
            if len(final_arr) == 0 :
                final_arr = ascii_data_array
            else :
                final_arr = np.add(final_arr, ascii_data_array)
    
    print("merged")
    GenerateGridLookup(gridFile, outFile, final_arr, header.ascci_cols, header.ascii_rows)

@dataclass
class AsciiHeader:
    ascii_path: str
    ascci_cols: int
    ascii_rows: int
    ascii_xll: float
    ascii_yll: float
    ascii_cs: float
    ascii_nodata: float
    image_extent: list

def readAsciiHeader(ascii_path) :
    if ascii_path.endswith(".gz") :
           # Read in ascii header data
        with gzip.open(ascii_path, 'rt') as source:
            ascii_header = source.readlines()[:6] 
    else :
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

    image_extent = [
                ascii_xll, ascii_xll + ascci_cols * ascii_cs,
                ascii_yll, ascii_yll + ascii_rows * ascii_cs] 

    return AsciiHeader(ascii_path, ascci_cols, ascii_rows, ascii_xll, ascii_yll, ascii_cs, ascii_nodata, image_extent)

def GenerateGridLookup(gridsource, outFile, npArr, colsLon, rowsLat) :
    outGridHeader = "Column,Row,latitude,longitude,irrigation\n"
    with open(outFile, mode="wt", newline="") as outGridfile :
        outGridfile.writelines(outGridHeader)
        with open(gridsource) as sourcefile:
            firstLine = True
            colID = -1
            rowID = -1
            latID = -1
            lonID = -1
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
                        if token == "latitude" :
                            latID = index
                        if token == "longitude" :
                            lonID = index
                else :
                    col = int(tokens[colID])
                    row = int(tokens[rowID])
                    lat = float(tokens[latID])
                    lon = float(tokens[lonID])
                    # calculate position of lon/lat in array
                    arrPosCol = ((colsLon//2) + int(lon*12.))
                    arrPosRow = ((rowsLat//2) + int(-1*lat*12.))
                    value = npArr[arrPosRow][arrPosCol]
                    isIrrigated = 0
                    if value > 0 :
                        isIrrigated = 1
                    outline = [str(col), #col 
                                str(row), #row
                                str(lat), #lat
                                str(lon), #long
                                str(isIrrigated) #irrigated
                                ]
                    outGridfile.writelines(",".join(outline) + "\n")

if __name__ == "__main__":
    build()
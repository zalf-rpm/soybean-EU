#!/usr/bin/python
# -*- coding: UTF-8

import gzip
from dataclasses import dataclass
import os
import numpy as np
import math

def build() :
    "main"

    asciiYieldfutuT1 = "./extract_stats/eval/dev_max_yield_future_trnoT1.asc.gz"
    asciiYieldfutuT2 = "./extract_stats/eval/dev_max_yield_future_trnoT2.asc.gz"
    asciiYieldhistT1 = "./extract_stats/eval/dev_max_yield_historical_trnoT1.asc.gz"
    asciiYieldhistT2 = "./extract_stats/eval/dev_max_yield_historical_trnoT2.asc.gz"

    def readFile(file) :
        print("File:", file)
        header = readAsciiHeader(file)
        ascii_data_array = np.loadtxt(header.ascii_path, dtype=np.float, skiprows=6)
        # Set the nodata values to nan
        ascii_data_array[ascii_data_array == header.ascii_nodata] = np.nan
        #print(file)
        #print("area:", np.count_nonzero(~np.isnan(ascii_data_array)), "(1x1km pixel)")
        ascii_data_array[ascii_data_array == 0] = np.nan
        #print("evaluated area:", np.count_nonzero(~np.isnan(ascii_data_array)), "(1x1km pixel)")
        return ascii_data_array

    arrYieldfutuT1 = readFile(asciiYieldfutuT1)
    arrYieldfutuT2 = readFile(asciiYieldfutuT2)
    arrYieldhistT1 = readFile(asciiYieldhistT1)
    arrYieldhistT2 = readFile(asciiYieldhistT2)

# # for visualization
#     print("max:")
#     print("future T1:", np.nanmax(arrYieldfutuT1))
#     print("future T2:", np.nanmax(arrYieldfutuT2))
#     print("hist T1:", np.nanmax(arrYieldhistT1))
#     print("hist T2:", np.nanmax(arrYieldhistT2))
 

 # 1) Durchschnittlicher Ertrag pro Hektar, einem für die beregneten, einmal für die unberegneten und einmal für alle Soja-Flächen. 
 # AVG max yield - irrigated/rainfed historical - future

    avgYieldfutuT1 = np.nanmean(arrYieldfutuT1)
    avgYieldfutuT2 = np.nanmean(arrYieldfutuT2)
    avgYieldhistT1 = np.nanmean(arrYieldhistT1)
    avgYieldhistT2 = np.nanmean(arrYieldhistT2)

    avgYieldfuture = np.nanmean(np.concatenate((arrYieldfutuT1, arrYieldfutuT2), axis=None))
    avgYieldhistorcal = np.nanmean(np.concatenate((arrYieldhistT1, arrYieldhistT2), axis=None))

 # 2) Die Soja-Fläche in der Baseline und die Soja-Fläche in der Zukunft 
 # Area historical - future (irr/rainfed)

    areaYieldfutuT1 = np.count_nonzero(~np.isnan(arrYieldfutuT1))
    areaYieldfutuT2 = np.count_nonzero(~np.isnan(arrYieldfutuT2))
    areaYieldhistT1 = np.count_nonzero(~np.isnan(arrYieldhistT1))
    areaYieldhistT2 = np.count_nonzero(~np.isnan(arrYieldhistT2))

 # 3) den durchschnittlichen Ertrag pro Fläche auf den Soja-Flächen der Baseline im Vergleich mit genau diesen Flächen in der Zukunft (flächentreu) und den durchschnittlichen Ertrag pro Fläche auf den Flächen die in der Zukunft neu hinzugekommen sind.
    
    def avgIntersection(future, historical) :
        numrows = len(historical)    # 3 rows in your example
        numcols = len(historical[0])
        counter = 0
        sum = 0
        
        for r in range(numrows) :
            for c in range(numcols) :
                if not math.isnan(historical[r][c]):
                    counter += 1
                    if not math.isnan(future[r][c]) :
                        sum += future[r][c]
        avg = 0
        if counter > 0 :
            avg = sum / counter
        return avg

    areaYieldT1 = avgIntersection(arrYieldfutuT1, arrYieldhistT1)
    areaYieldT2 = avgIntersection(arrYieldfutuT2, arrYieldhistT2)

    def avgIntersectionOuter(future, historical) :
        numrows = len(historical)    # 3 rows in your example
        numcols = len(historical[0])
        counter = 0
        sum = 0
        for r in range(numrows) :
            for c in range(numcols) :
                if not math.isnan(future[r][c]) and math.isnan(historical[r][c]):
                    counter += 1
                    sum += future[r][c]
        avg = 0
        if counter > 0 :
            avg = sum / counter
        return avg

    areaYieldAddT1 = avgIntersectionOuter(arrYieldfutuT1, arrYieldhistT1)
    areaYieldAddT2 = avgIntersectionOuter(arrYieldfutuT2, arrYieldhistT2)

    print("Average Yield future T1:    ",  int(avgYieldfutuT1), "[t ha-1]")
    print("Average Yield future T2:    ",  int(avgYieldfutuT2), "[t ha-1]")
    print("Average Yield historical T1:",  int(avgYieldhistT1), "[t ha-1]")
    print("Average Yield historical T2:",  int(avgYieldhistT2), "[t ha-1]")

    print("Average Yield future:       ", int(avgYieldfuture), "[t ha-1]")
    print("Average Yield historical:   ", int(avgYieldhistorcal), "[t ha-1]")

    print("Soybean Area future T1:     " ,areaYieldfutuT1,"(1x1km pixel)")
    print("Soybean Area future T2:     " ,areaYieldfutuT2,"(1x1km pixel)")
    print("Soybean Area historical T1: ", areaYieldhistT1, "(1x1km pixel)")
    print("Soybean Area historical T2: ", areaYieldhistT2, "(1x1km pixel)")

    print("Future Yield on baseline T1:", int(areaYieldT1), "[t ha-1]")
    print("Future Yield on baseline T2:", int(areaYieldT2), "[t ha-1]")
    print("Future Yield addition T1:   ", int(areaYieldAddT1), "[t ha-1]")
    print("Future Yield addition T2:   ", int(areaYieldAddT2), "[t ha-1]")

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


if __name__ == "__main__":
    build()
#!/usr/bin/python
# -*- coding: UTF-8

from pyproj import Proj, Transformer
from scipy.interpolate import NearestNDInterpolator
import numpy as np
import geopy.distance

def extractGridData() :

    files = ["missingregions.csv", "gridcells_altitude_ZALF-DK94-DK59.csv"]
    extRow, extCol = 1, 1
    entries = dict()
    for file in files :
        with open(file) as sourcefile:
            firstLine = True
            header = dict()
            for line in sourcefile:
                if firstLine :
                    firstLine = False
                    header = ReadHeader(line)
                    continue
                lineContent = loadLine(line, header)
                entries[(lineContent["row"], lineContent["col"])] = (lineContent["lon"], lineContent["lat"], lineContent["alti"])
                if extRow < lineContent["row"] +1 :
                    extRow = lineContent["row"] + 1
                if extCol < lineContent["col"] + 1 :
                    extCol = lineContent["col"] + 1

    wgs84 = Proj(init="epsg:4326") #proj4 -> (World Geodetic System 1984 https://epsg.io/4326)
    etrs89 = Proj(init="EPSG:3035") 
    transformer = Transformer.from_proj(wgs84, etrs89) 
    climaGridInterpolator = mapSoilMapping(entries, transformer)

    outGridHeader = "Column_,Row,Grid_Code,Location,elevation,latitude,longitude,soil_ref\n"
    outSoilHeader = "soil_ref,CLocation,latitude,depth,OC_topsoil,OC_subsoil,BD_topsoil,BD_subsoil,Sand_topsoil,Clay_topsoil,Silt_topsoil,Sand_subsoil,Clay_subsoil,Silt_subsoil\n"
    soildIdNumber = 0
    soilLookup = dict()
    with open("stu_eu_layer_grid.csv", mode="wt", newline="") as outGridfile :
        outGridfile.writelines(outGridHeader)
        with open("stu_eu_layer_ref.csv", mode="wt", newline="") as outSoilfile :
            outSoilfile.writelines(outSoilHeader)
            # read soil data
            with open("stu_eu_layers.csv") as sourcefile:
                firstLine = True
                soilheader = dict()
                for line in sourcefile:
                    if firstLine :
                        firstLine = False
                        soilheader = ReadSoilHeader(line)
                        continue
                    outLineDist = loadSoilLine(line, soilheader,entries, transformer, climaGridInterpolator)
                    out = outLineDist[0]
                    distance = outLineDist[1]
                    if distance < 25 : # write only line where we found appropriate climate grid cells
                        soilId = ("{0}_{1:03d}".format(out[3][0], out[3][1]), #climate location
                        out[5+soilheader["depth"]],
                        out[5+soilheader["OC_topsoil"]],
                        out[5+soilheader["OC_subsoil"]],
                        out[5+soilheader["BD_topsoil"]],
                        out[5+soilheader["BD_subsoil"]],
                        out[5+soilheader["Sand_topsoil"]],
                        out[5+soilheader["Clay_topsoil"]],
                        out[5+soilheader["Silt_topsoil"]],
                        out[5+soilheader["Sand_subsoil"]],
                        out[5+soilheader["Clay_subsoil"]],
                        out[5+soilheader["Silt_subsoil"]])

                        if not soilId in soilLookup : 
                            soildIdNumber += 1                           
                            soilLookup[soilId] = soildIdNumber
                            outlineSoil = [str(soildIdNumber),
                                "{0}_{1:03d}".format(out[3][0], out[3][1]), #climate location
                                str(out[2]), #lat
                                out[5+soilheader["depth"]],
                                out[5+soilheader["OC_topsoil"]],
                                out[5+soilheader["OC_subsoil"]],
                                out[5+soilheader["BD_topsoil"]],
                                out[5+soilheader["BD_subsoil"]],
                                out[5+soilheader["Sand_topsoil"]],
                                out[5+soilheader["Clay_topsoil"]],
                                out[5+soilheader["Silt_topsoil"]],
                                out[5+soilheader["Sand_subsoil"]],
                                out[5+soilheader["Clay_subsoil"]],
                                out[5+soilheader["Silt_subsoil"]]]
                            outSoilfile.writelines(",".join(outlineSoil) + "\n")

                        outline = [str(out[0][1]), #col 
                                str(out[0][0]), #row
                                "{0}{1:02d}".format(out[0][0], out[0][1]),#gridcode
                                "{0}_{1}".format(out[0][0], out[0][1]), #location
                                str(out[4]), #elevation
                                str(out[2]), #lat
                                str(out[1]), #long
                                str(soilLookup[soilId]) 
                                ]
                        outGridfile.writelines(",".join(outline) + "\n")

def mapSoilMapping(climate_listMapping, transformer) :
    points = []
    values = []
    for key in climate_listMapping:
        row, col = key[0], key[1]
        clat, clon = climate_listMapping[key][1], climate_listMapping[key][0]
        try:
            cr_geoTargetGrid, ch_geoTargetGrid = transformer.transform(clon, clat)
            points.append([cr_geoTargetGrid, ch_geoTargetGrid])
            values.append((row, col))
        except:
            print("mist:", clon, clat, row, col)
            continue

    return NearestNDInterpolator(np.array(points), np.array(values))

def newGrid(extRow, extCol, defaultVal) :
    grid = [defaultVal] * extRow
    for i in range(extRow) :
        grid[i] = [defaultVal] * extCol
    return grid


def ReadHeader(line) : 
    #read header
    #"GRID_NO","LATITUDE","LONGITUDE","ALTITUDE","DAY","TEMPERATURE_MAX","TEMPERATURE_MIN","TEMPERATURE_AVG","WINDSPEED","VAPOURPRESSURE","PRECIPITATION","RADIATION"
    #GRID_NO,LATITUDE,LONGITUDE,ALTITUDE
    tokens = line.split(",")
    outDic = dict()
    i = -1
    for token in tokens :
        token = token.strip('\"')
        token = token.strip()
        i = i+1
        if token == "LATITUDE":
            outDic["lat"] = i
        if token == "LONGITUDE":
            outDic["lon"] = i
        if token == "GRID_NO" : 
            outDic["grid_no"] = i
        if token == "ALTITUDE" : 
            outDic["alti"] = i

    return outDic

SOIL_COLUMN_NAMES = ["col","row","elevation","latitude","longitude","depth","OC_topsoil","OC_subsoil","BD_topsoil","BD_subsoil","Sand_topsoil","Clay_topsoil","Silt_topsoil","Sand_subsoil","Clay_subsoil","Silt_subsoil"]

def ReadSoilHeader(line) : 
    #col,row,elevation,latitude,longitude,depth,OC_topsoil,OC_subsoil,BD_topsoil,BD_subsoil,Sand_topsoil,Clay_topsoil,Silt_topsoil,Sand_subsoil,Clay_subsoil,Silt_subsoil
    colDic = dict()
    tokens = line.split(",")
    i = -1
    for token in tokens :
        token = token.strip()
        i = i+1
        if token in SOIL_COLUMN_NAMES :
            colDic[token] = i
    return colDic

def loadSoilLine(line, header, climateEntries, transformer, climaGridInterpolator) :
    # read relevant content from line 
    tokens = line.split(",")
    row = int(tokens[header["row"]])
    col = int(tokens[header["col"]])
    slon = float(tokens[header["longitude"]])
    slat = float(tokens[header["latitude"]]) 

    soilr_geoTargetGrid, soilh_geoTargetGrid = transformer.transform(slon, slat)
    crow, ccol = climaGridInterpolator(soilr_geoTargetGrid, soilh_geoTargetGrid)


    # double check distances
    coords_1 = (slat, slon)
    coords_2 = (climateEntries[(crow, ccol)][1], climateEntries[(crow, ccol)][0])
    distance = geopy.distance.vincenty(coords_1, coords_2).km

    numCOl = len(SOIL_COLUMN_NAMES)
    out = [""] * (numCOl + 5)
    out[0] = (row, col)
    out[1] = slon
    out[2] = slat
    out[3] = (crow, ccol)
    out[4] = (climateEntries[(crow, ccol)][2])    
    for i in range(5, numCOl+5):
        out[i] = tokens[i-5].strip()
    return (out, distance)

def loadLine(line, header) :
    # read relevant content from line 
    tokens = line.split(",")
    gridIdx = tokens[header["grid_no"]] 
    row = int(gridIdx[:-3])
    col = int(gridIdx[-3:])
    lonIdx = float(tokens[header["lon"]])
    latIdx = float(tokens[header["lat"]]) 
    altiIdx = int(tokens[header["alti"]])
    outDic = {
        "grid_no": gridIdx,
        "row": row,
        "col": col,
        "lon": lonIdx,
        "lat": latIdx,
        "alti": altiIdx,
    }

    return outDic

if __name__ == "__main__":
    extractGridData()
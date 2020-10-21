

#!/usr/bin/python
# -*- coding: UTF-8

pathSoilLayerFile = "../stu_eu_layer_ref.csv"
pathSoilLookupFile = "./soil_lookup.csv"
pathoutLookupFile = "./stu_eu_hermes_batch_lookup.csv"

def writeLookupFile() :
    
    lookup = dict()
    with open(pathSoilLookupFile) as lookupfile: 
        firstLine = True        
        for line in lookupfile:
            if firstLine :
                firstLine = False
                continue
            tokens = line.split(",")
            lookup[tokens[0]] = tokens[1].strip()

    lookupAlti = dict()
    files = ["../missingregions.csv", "../gridcells_altitude_ZALF-DK94-DK59.csv"]
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
                fcode = lineContent[0]
                alti = lineContent[1]
                lookupAlti[fcode] = alti
                
    with open(pathoutLookupFile, mode="wt", newline="") as outlookupfile :
        # read soil data
        with open(pathSoilLayerFile) as sourcefile:
            outlookupfile.writelines("soil_ref,sid,fcode,latitude,altitude\n")
            firstLine = True
            soilheader = dict()
            for line in sourcefile:
                if firstLine :
                    firstLine = False
                    soilheader = ReadSoilHeader(line)
                    continue
                out = loadSoilLine(line)
                soil_ref = out[soilheader["soil_ref"]]
                sid = lookup[soil_ref]
                fcode = out[soilheader["CLocation"]]
                Lat = out[soilheader["latitude"]]
                altitude = lookupAlti[fcode]
                outline = [
                    soil_ref,
                    sid,
                    fcode,
                    Lat,
                    altitude,
                ]
                                
                outlookupfile.writelines(",".join(outline) + "\n")


def loadSoilLine(line) :
    # read relevant content from line 
    tokens = line.split(",")
    numCOl = len(tokens) 
    out = [""] * (numCOl)
    for i in range(numCOl):
        out[i] = tokens[i].strip()
    return out

def ReadSoilHeader(line) : 
    colDic = dict()
    tokens = line.split(",")
    i = -1
    for token in tokens :
        token = token.strip()
        i = i+1
        colDic[token] = i
    return colDic

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

def loadLine(line, header) :
    # read relevant content from line 
    tokens = line.split(",")
    gridIdx = tokens[header["grid_no"]] 
    row = int(gridIdx[:-3])
    col = int(gridIdx[-3:])
    fstr = "{0:d}_{1:03d}"
    cLocation = fstr.format(row, col) #climate location
    alti = tokens[header["alti"]].strip()

    return cLocation, alti


if __name__ == "__main__":
    writeLookupFile()
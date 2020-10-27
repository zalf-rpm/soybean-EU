#!/usr/bin/python
# -*- coding: UTF-8

outFile = "./stu_eu_layer_grid.csv"
sidFile = "./hermes/soil_lookup.csv"
lat_lon_up = (52.629653, 13.926220)
lat_lon_down = (52.445819, 14.262035)

def findAllSoilRef() :

    outSet = set()
    with open(outFile) as sourcefile:
        #Column_,Row,Grid_Code,Location,elevation,latitude,longitude,soil_ref
        firstLine = True
        header = dict()
        for line in sourcefile:
            if firstLine :
                firstLine = False
                header = ReadHeader(line)
                continue

            out = loadLine(line)
            latitude = float(out[header["latitude"]])
            longitude = float(out[header["longitude"]])
            soil_ref = out[header["soil_ref"]]

            if latitude <= lat_lon_up[0] and latitude >= lat_lon_down[0] and longitude >= lat_lon_up[1] and longitude <= lat_lon_down[1] :
                outSet.add(soil_ref)

    with open(sidFile) as sourcefile:
        #soil_ref,SID
        firstLine = True
        header = dict()
        for line in sourcefile:
            if firstLine :
                firstLine = False
                header = ReadHeader(line)
                continue
            out = loadLine(line)
            soil_ref = out[header["soil_ref"]]
            SID = out[header["SID"]]
            if soil_ref in outSet :
                print(soil_ref, SID )

#     for item in outSet :
#             print(item)


def ReadHeader(line) : 
    colDic = dict()
    tokens = line.split(",")
    i = -1
    for token in tokens :
        token = token.strip()
        i = i+1
        colDic[token] = i
    return colDic

def loadLine(line) :
    # read relevant content from line 
    tokens = line.split(",")
    numCOl = len(tokens) 
    out = [""] * (numCOl)
    for i in range(numCOl):
        out[i] = tokens[i].strip()
    return out

if __name__ == "__main__":
    findAllSoilRef()
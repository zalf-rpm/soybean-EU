#!/usr/bin/python
# -*- coding: UTF-8

outFile = "./stu_eu_layer_grid.csv"
#sidFile = "./hermes/soil_lookup.csv"
grid_up = (4074-1800, 1800)
grid_down = (4074-1600, 3750)

#nrows = 4074
#ncols = 4583


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
            col = int(out[header["Column_"]])
            row = int(out[header["Row"]])
            soil_ref = out[header["soil_ref"]]

            if row >= grid_up[0] and row <= grid_down[0] and col >= grid_up[1] and col <= grid_down[1] :
                outSet.add(soil_ref)

    # with open(sidFile) as sourcefile:
    #     #soil_ref,SID
    #     firstLine = True
    #     header = dict()
    #     for line in sourcefile:
    #         if firstLine :
    #             firstLine = False
    #             header = ReadHeader(line)
    #             continue
    #         out = loadLine(line)
    #         soil_ref = out[header["soil_ref"]]
    #         SID = out[header["SID"]]
    #         if soil_ref in outSet :
    #             print(soil_ref, SID )
    
    outList = sorted(outSet)
    #print(outList)
    for item in outList :
        print(item)


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
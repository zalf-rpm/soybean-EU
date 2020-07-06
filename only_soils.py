#!/usr/bin/python
# -*- coding: UTF-8

def extractGridData() :

    outSoilHeader = "id,depth,OC_topsoil,OC_subsoil,BD_topsoil,BD_subsoil,Sand_topsoil,Clay_topsoil,Silt_topsoil,Sand_subsoil,Clay_subsoil,Silt_subsoil\n"
    soildIdNumber = 0
    soilLookup = dict()
    with open("stu_eu_layer_soils.csv", mode="wt", newline="") as outGridfile :
        outGridfile.writelines(outSoilHeader)
        # read soil data
        with open("stu_eu_layer_ref.csv") as sourcefile:
            firstLine = True
            for line in sourcefile:
                if firstLine :
                    firstLine = False
                    soilheader = ReadSoilHeader(line)
                    continue
                outLineDist = loadSoilLine(line, soilheader)
                out = outLineDist
                soilId = (
                out[soilheader["depth"]],
                out[soilheader["OC_topsoil"]],
                out[soilheader["OC_subsoil"]],
                out[soilheader["BD_topsoil"]],
                out[soilheader["BD_subsoil"]],
                out[soilheader["Sand_topsoil"]],
                out[soilheader["Clay_topsoil"]],
                out[soilheader["Silt_topsoil"]],
                out[soilheader["Sand_subsoil"]],
                out[soilheader["Clay_subsoil"]],
                out[soilheader["Silt_subsoil"]])

                if not soilId in soilLookup : 
                    soildIdNumber += 1                           
                    soilLookup[soilId] = soildIdNumber
                    outlineSoil = [str(soildIdNumber),
                        out[soilheader["depth"]],
                        out[soilheader["OC_topsoil"]],
                        out[soilheader["OC_subsoil"]],
                        out[soilheader["BD_topsoil"]],
                        out[soilheader["BD_subsoil"]],
                        out[soilheader["Sand_topsoil"]],
                        out[soilheader["Clay_topsoil"]],
                        out[soilheader["Silt_topsoil"]],
                        out[soilheader["Sand_subsoil"]],
                        out[soilheader["Clay_subsoil"]],
                        out[soilheader["Silt_subsoil"]]]
                    outGridfile.writelines(",".join(outlineSoil) + "\n")

SOIL_COLUMN_NAMES = ["soil_ref","CLocation","latitude","depth","OC_topsoil","OC_subsoil","BD_topsoil","BD_subsoil","Sand_topsoil","Clay_topsoil","Silt_topsoil","Sand_subsoil","Clay_subsoil","Silt_subsoil"]

def ReadSoilHeader(line) : 
    #soil_ref,CLocation,latitude,depth,OC_topsoil,OC_subsoil,BD_topsoil,BD_subsoil,Sand_topsoil,Clay_topsoil,Silt_topsoil,Sand_subsoil,Clay_subsoil,Silt_subsoil
    colDic = dict()
    tokens = line.split(",")
    i = -1
    for token in tokens :
        token = token.strip()
        i = i+1
        if token in SOIL_COLUMN_NAMES :
            colDic[token] = i
    return colDic

def loadSoilLine(line, header) :
    # read relevant content from line 
    tokens = line.split(",")

    numCOl = len(SOIL_COLUMN_NAMES) 
    out = [""] * (numCOl)
    for i in range(numCOl):
        out[i] = tokens[i].strip()
    return out


if __name__ == "__main__":
    extractGridData()
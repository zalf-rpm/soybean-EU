#!/usr/bin/python
# -*- coding: UTF-8

def extractGridData() :

    # PWP,FC,SAT,SWinit,
    outSoilHeader = "id,depth,OC_topsoil,OC_subsoil,BD_topsoil,BD_subsoil,Sand_topsoil,Clay_topsoil,Silt_topsoil,Sand_subsoil,Clay_subsoil,Silt_subsoil,Texture_topsoil,Texture_subsoil,PWP,FC\n"
    soildIdNumber = 0
    soilLookup = dict()
    with open("stu_eu_layer_soils.csv", mode="wt", newline="") as outGridfile :
        outGridfile.writelines(outSoilHeader)
        # read soil data
        with open("stu_eu_layer_ref.csv") as sourcefile:
            firstLine = True
            soilheader = dict()
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
                    
                    # calc texture
                    clayTS = float(out[soilheader["Clay_topsoil"]])
                    sandTS = float(out[soilheader["Sand_topsoil"]])
                    siltTS = float(out[soilheader["Silt_topsoil"]])
                    textTS = sand_and_clay_to_ka5_texture(sandTS/100.0, clayTS/100.0)
                    claySS = float(out[soilheader["Clay_subsoil"]])
                    sandSS = float(out[soilheader["Sand_subsoil"]])
                    textSS = sand_and_clay_to_ka5_texture(sandSS/100.0, claySS/100.0)

                    cOrgTS = float(out[soilheader["OC_topsoil"]])


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
                        out[soilheader["Silt_subsoil"]],
                        textTS,
                        textSS,
                        "{:1.3f}".format(calcPWP(cOrgTS, sandTS, siltTS)),
                        "{:1.3f}".format(calcFK(cOrgTS, sandTS, siltTS )),
                        ]

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

# PTF nach Toth 2015
#FK:  Let W(LT)    = 0.2449 - 0.1887 * (1/(CGEHALT(1)+1)) + 0.004527 * Ton(1) + 0.001535 * SLUF(1) + 0.001442 * SLUF(1) * (1/(CGEHALT(1)+1)) - 0.0000511 * SLUF(1) * Ton(1) + 0.0008676 * Ton(1) * (1/(CGEHALT(1)+1))
def calcFK(cgehalt, ton, sluf ) :
     return  0.2449 - 0.1887 * (1/(cgehalt+1)) + 0.004527 * ton + 0.001535 * sluf + 0.001442 * sluf * (1/(cgehalt+1)) - 0.0000511 * sluf * ton + 0.0008676 * ton * (1/(cgehalt+1))
# PWP: Let WMIN(LT) = 0.09878 + 0.002127* Ton(1) - 0.0008366 *SLUF(1) - 0.0767 *(1/(CGEHALT(1)+1)) + 0.00003853 * SLUF(1) * Ton(1) + 0.00233 * SLUF(1) * (1/(CGEHALT(1)+1)) + 0.0009498 * SLUF(1) * (1/(CGEHALT(1)+1))
def calcPWP(cgehalt, ton, sluf) :
    return 0.09878 + 0.002127* ton - 0.0008366 *sluf - 0.0767 *(1/(cgehalt+1)) + 0.00003853 * sluf * ton + 0.00233 * sluf * (1/(cgehalt+1)) + 0.0009498 * sluf * (1/(cgehalt+1))


def sand_and_clay_to_ka5_texture(sand, clay):
    "get a rough KA5 soil texture class from given sand and soil content"
    silt = 1.0 - sand - clay
    soil_texture = ""

    if silt < 0.1 and clay < 0.05:
        soil_texture = "Ss"
    elif silt < 0.25 and clay < 0.05:
        soil_texture = "Su2"
    elif silt < 0.25 and clay < 0.08:
        soil_texture = "Sl2"
    elif silt < 0.40 and clay < 0.08:
        soil_texture = "Su3"
    elif silt < 0.50 and clay < 0.08:
        soil_texture = "Su4"
    elif silt < 0.8 and clay < 0.08:
        soil_texture = "Us"
    elif silt >= 0.8 and clay < 0.08:
        soil_texture = "Uu"
    elif silt < 0.1 and clay < 0.17:
        soil_texture = "St2"
    elif silt < 0.4 and clay < 0.12:
        soil_texture = "Sl3"
    elif silt < 0.4 and clay < 0.17:
        soil_texture = "Sl4"
    elif silt < 0.5 and clay < 0.17:
        soil_texture = "Slu"
    elif silt < 0.65 and clay < 0.17:
        soil_texture = "Uls"
    elif silt >= 0.65 and clay < 0.12:
        soil_texture = "Ut2"
    elif silt >= 0.65 and clay < 0.17:
        soil_texture = "Ut3"
    elif silt < 0.15 and clay < 0.25:
        soil_texture = "St3"
    elif silt < 0.30 and clay < 0.25:
        soil_texture = "Ls4"
    elif silt < 0.40 and clay < 0.25:
        soil_texture = "Ls3"
    elif silt < 0.50 and clay < 0.25:
        soil_texture = "Ls2"
    elif silt < 0.65 and clay < 0.30:
        soil_texture = "Lu"
    elif silt >= 0.65 and clay < 0.25:
        soil_texture = "Ut4"
    elif silt < 0.15 and clay < 0.35:
        soil_texture = "Ts4"
    elif silt < 0.30 and clay < 0.45:
        soil_texture = "Lts"
    elif silt < 0.50 and clay < 0.35:
        soil_texture = "Lt2"
    elif silt < 0.65 and clay < 0.45:
        soil_texture = "Tu3"
    elif silt >= 0.65 and clay >= 0.25:
        soil_texture = "Tu4"
    elif silt < 0.15 and clay < 0.45:
        soil_texture = "Ts3"
    elif silt < 0.50 and clay < 0.45:
        soil_texture = "Lt3"
    elif silt < 0.15 and clay < 0.65:
        soil_texture = "Ts2"
    elif silt < 0.30 and clay < 0.65:
        soil_texture = "Tl"
    elif silt >= 0.30 and clay < 0.65:
        soil_texture = "Tu2"
    elif clay >= 0.65:
        soil_texture = "Tt"
    else:
        soil_texture = ""

    return soil_texture



if __name__ == "__main__":
    extractGridData()
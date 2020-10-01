#!/usr/bin/python
# -*- coding: UTF-8

pathSoilLayerFile = "../stu_eu_layer_ref.csv"
pathOutputFile = "./project/soyeu/soil_soyeu.txt"
pathSoilLookupFile = "./soil_lookup.csv"

def extractGridData() :

    outSoilHeader = "SID Corg Te  lb B St C/N C/S Hy Rd NuHo  FC WP PS S% SI% C% lamda DraiT  Drai% GW LBG\n"
    lookupRefHeader = "soil_ref,SID,soil_layer\n"
    soildIdNumber = 0
    soilLookup = dict()
    soilLayerLookup = dict()
    with open(pathOutputFile, mode="wt", newline="") as outSoilfile :
        outSoilfile.writelines(outSoilHeader)
        with open(pathSoilLookupFile, mode="wt", newline="") as outLookupFile :
            outLookupFile.writelines(lookupRefHeader)
            # read soil data
            with open(pathSoilLayerFile) as sourcefile:
                firstLine = True
                soilheader = dict()
                for line in sourcefile:
                    if firstLine :
                        firstLine = False
                        soilheader = ReadSoilHeader(line)
                        continue
                    out = loadSoilLine(line)
                    soilId = (out[soilheader["depth"]],
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
                        claySS = float(out[soilheader["Clay_subsoil"]])
                        sandSS = float(out[soilheader["Sand_subsoil"]])
                        siltSS = float(out[soilheader["Silt_subsoil"]])
                        textSS = sand_and_clay_to_ka5_texture(sandSS/100.0, claySS/100.0)
                        clayTS = float(out[soilheader["Clay_topsoil"]])
                        sandTS = float(out[soilheader["Sand_topsoil"]])
                        siltTS = float(out[soilheader["Silt_topsoil"]])
                        textTS = sand_and_clay_to_ka5_texture(sandTS/100.0, clayTS/100.0)
                        cOrgTS = float(out[soilheader["OC_topsoil"]])
                        cOrgSS = float(out[soilheader["OC_subsoil"]])
                        cOrgTSstr = "{:1.2f}".format(cOrgTS) if cOrgTS < 10 else "{:1.1f}".format(cOrgTS)
                        cOrgSSstr = "{:1.2f}".format(cOrgSS) if cOrgSS < 10 else "{:1.1f}".format(cOrgSS)
    
                        rootDepth = float(out[soilheader["depth"]]) * 10 # in cm
    
                        hasSecondLayer = claySS + sandSS + siltSS > 0
                        numberOfHorizons = "02  " if hasSecondLayer else "01  "
                        bulkDensityTS = float(out[soilheader["BD_topsoil"]])
                        bulkDensityClassTS = getBulkDensityClass(bulkDensityTS) 
                        bulkDensitySS = float(out[soilheader["BD_subsoil"]])
                        bulkDensityClassSS = getBulkDensityClass(bulkDensitySS) 
                        soilLayerLookup[soildIdNumber] = 2 if hasSecondLayer else 1
                        # layer 1
                        outlineSoil = [
                            "{:03d}".format(soildIdNumber), # SID
                            cOrgTSstr,                      #Corg
                            textTS,                         #Te
                            "03",                           #lb
                            str(bulkDensityClassTS),        #B
                            "00",                           #St
                            "10",                           #C/N
                            "    ",                         #C/S
                            "00",                           #Hy
                            "{:02.0f}".format(rootDepth),   #Rd
                            numberOfHorizons,               #NuHo
                            "{:2.0f}".format(calcFK(cOrgTS, sandTS, siltTS )*100), #FC 
                            "{:2.0f}".format(calcPWP(cOrgTS, sandTS, siltTS)*100), #WP 
                            "{:2.0f}".format(getPoreVolume(bulkDensityTS)*100),    #PS 
                            "{:02d}".format(int(out[soilheader["Sand_topsoil"]])), #S% 
                            "{:02d}".format(int(out[soilheader["Silt_topsoil"]])), #SI% 
                            "{:02d}".format(int(out[soilheader["Clay_topsoil"]])), #C%
                            "00",                           #lamda 
                            " 20 ",                         #DraiT  
                            " 00",                          #Drai% 
                            " 99",                          #GW 
                            "01",                           #LBG 
                            ]
                        outSoilfile.writelines(" ".join(outlineSoil) + "\n")
    
                        # layer 2
                        if hasSecondLayer :
                            # second layer
                            outlineSoil = [
                                "{:03d}".format(soildIdNumber), # SID
                                cOrgSSstr,                      #Corg
                                textSS,                         #Te
                                "20",                           #lb
                                str(bulkDensityClassSS),        #B
                                "00",                           #St
                                "10",                           #C/N
                                "    ",                         #C/S
                                "00",                           #Hy
                                "  ",                           #Rd
                                "    ",                         #NuHo
                                "{:2.0f}".format(calcFK(cOrgSS, sandSS, siltSS )*100), #FC 
                                "{:2.0f}".format(calcPWP(cOrgSS, sandSS, siltSS)*100), #WP 
                                "{:2.0f}".format(getPoreVolume(bulkDensitySS)*100),    #PS 
                                "{:02d}".format(int(out[soilheader["Sand_subsoil"]])), #S% 
                                "{:02d}".format(int(out[soilheader["Silt_subsoil"]])), #SI% 
                                "{:02d}".format(int(out[soilheader["Clay_subsoil"]])), #C%
                                "00",                           #lamda 
                                " 20 ",                         #DraiT  
                                " 00",                          #Drai% 
                                "   ",                          #GW 
                                "  ",                           #LBG 
                                ]
                            outSoilfile.writelines(" ".join(outlineSoil) + "\n")
                        
                    outLookupFile.writelines("{0},{1:03d},{2:d}\n".format(out[soilheader["soil_ref"]], soilLookup[soilId], soilLayerLookup[soilLookup[soilId]]))    

#SOIL_COLUMN_NAMES = ["col","row","elevation","latitude","longitude","depth","OC_topsoil","OC_subsoil","BD_topsoil","BD_subsoil","Sand_topsoil","Clay_topsoil","Silt_topsoil","Sand_subsoil","Clay_subsoil","Silt_subsoil"]

def ReadSoilHeader(line) : 
    #col,row,elevation,latitude,longitude,depth,OC_topsoil,OC_subsoil,BD_topsoil,BD_subsoil,Sand_topsoil,Clay_topsoil,Silt_topsoil,Sand_subsoil,Clay_subsoil,Silt_subsoil
    colDic = dict()
    tokens = line.split(",")
    i = -1
    for token in tokens :
        token = token.strip()
        i = i+1
        #if token in SOIL_COLUMN_NAMES :
        colDic[token] = i
    return colDic

def loadSoilLine(line) :
    # read relevant content from line 
    tokens = line.split(",")
    numCOl = len(tokens) 
    out = [""] * (numCOl)
    for i in range(numCOl):
        out[i] = tokens[i].strip()
    return out

def sand_and_clay_to_ka5_texture(sand, clay):
    "get a rough KA5 soil texture class from given sand and soil content"
    silt = 1.0 - sand - clay
    soil_texture = ""

    if silt < 0.1 and clay < 0.05:
        soil_texture = "Ss "
    elif silt < 0.25 and clay < 0.05:
        soil_texture = "Su2"
    elif silt < 0.25 and clay < 0.08:
        soil_texture = "Sl2"
    elif silt < 0.40 and clay < 0.08:
        soil_texture = "Su3"
    elif silt < 0.50 and clay < 0.08:
        soil_texture = "Su4"
    elif silt < 0.8 and clay < 0.08:
        soil_texture = "Us "
    elif silt >= 0.8 and clay < 0.08:
        soil_texture = "Uu "
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
        soil_texture = "Lu "
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
        soil_texture = "Tl "
    elif silt >= 0.30 and clay < 0.65:
        soil_texture = "Tu2"
    elif clay >= 0.65:
        soil_texture = "Tt "
    else:
        soil_texture = ""

    return soil_texture

def getPoreVolume(bulkDensity) :
    return 1 - (bulkDensity/1000) / 2.65

def getBulkDensityClass(bulkDensity) :
    bulkDensityClass = 1
    bd = bulkDensity / 1000
    if bd < 1.3 :
        bulkDensityClass = 1
    elif bd < 1.5 :
        bulkDensityClass = 2
    elif bd < 1.7 :
        bulkDensityClass = 3
    elif bd < 1.85 :
        bulkDensityClass = 4
    else :
        bulkDensityClass = 5
    return bulkDensityClass

# PTF nach Toth 2015
#FK:  Let W(LT)    = 0.2449 - 0.1887 * (1/(CGEHALT(1)+1)) + 0.004527 * Ton(1) + 0.001535 * SLUF(1) + 0.001442 * SLUF(1) * (1/(CGEHALT(1)+1)) - 0.0000511 * SLUF(1) * Ton(1) + 0.0008676 * Ton(1) * (1/(CGEHALT(1)+1))
def calcFK(cgehalt, ton, sluf ) :
     return  0.2449 - 0.1887 * (1/(cgehalt+1)) + 0.004527 * ton + 0.001535 * sluf + 0.001442 * sluf * (1/(cgehalt+1)) - 0.0000511 * sluf * ton + 0.0008676 * ton * (1/(cgehalt+1))
# PWP: Let WMIN(LT) = 0.09878 + 0.002127* Ton(1) - 0.0008366 *SLUF(1) - 0.0767 *(1/(CGEHALT(1)+1)) + 0.00003853 * SLUF(1) * Ton(1) + 0.00233 * SLUF(1) * (1/(CGEHALT(1)+1)) + 0.0009498 * SLUF(1) * (1/(CGEHALT(1)+1))
def calcPWP(cgehalt, ton, sluf) :
    val = 0.09878 + 0.002127 * ton - 0.0008366 * sluf - 0.0767 * (1/(cgehalt+1)) + 0.00003853 * sluf * ton + 0.00233 * sluf * (1/(cgehalt+1)) + 0.0009498 * sluf * (1/(cgehalt+1))
    return val


if __name__ == "__main__":
    extractGridData()
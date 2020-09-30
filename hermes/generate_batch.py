

#!/usr/bin/python
# -*- coding: UTF-8

project="soyeu" 
WeatherRootFolder="/beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected2" 
WeatherFolder=["0/0_0", "2/GFDL-CM3_45", "2/GISS-E2-R_45","2/HadGEM2-ES_45","2/MIROC5_45","2/MPI-ESM-MR_45"]
fileExtension="1" 
plotNrs=["10001", "10002"]
soilId="001" #
fcode="104_118" #
Altitude="90" #
Latitude="51.46" #
#poligonID="10411835001" #
AutoIrrigation=["1","0"] 
AutoIrrigationFolder=["Ir","noIr"]
resultfolder=["0_0_0", "2_GFDL-CM3_45", "2_GISS-E2-R_45","2_HadGEM2-ES_45","2_MIROC5_45","2_MPI-ESM-MR_45"]
maturityGroup = ["0", "00","000","0000","i","ii"]
paramfolderTmpl="./parameter_{0}"
resultfolderTemplate = "{0}/{1}/{2}/RESULT" # climateScenario/maturityGroup/irrigation
CO2concentration=["360","499","499","499","499","499"]
batchLine = "project={0} WeatherRootFolder={1} WeatherFolder={2} soilId={3} fcode={4} fileExtension={5} plotNr={6} Altitude={7} Latitude={8} poligonID={9} AutoIrrigation={10} CO2concentration={11} parameter={12} resultfolder={13}\n"


pathOutBatchFile = "./soyeu_all_{0}_batch.txt" 
pathSoilLayerFile = "../stu_eu_layer_ref.csv"
pathSoilLookupFile = "./soil_lookup.csv"


def writeBatchFile() :
    
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

    outfiles = [""] * len(resultfolder)
    for resultID in range(len(resultfolder)) : 
        resultName = resultfolder[resultID]   
        outfiles[resultID] = open(pathOutBatchFile.format(resultName), mode="wt", newline="")

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
            soil_ref = out[soilheader["soil_ref"]]
            sid = lookup[soil_ref]
            fcode = out[soilheader["CLocation"]]
            Lat = out[soilheader["latitude"]]
            altitude = lookupAlti[fcode]

            for resultID in range(len(resultfolder)) : 
                wfolder = WeatherFolder[resultID]
                co2 = CO2concentration[resultID]
                resultName = resultfolder[resultID]  
                for plotNr in plotNrs :
                    for irri in range(len(AutoIrrigation)) :
                        for mat in maturityGroup :
                            resultout = resultfolderTemplate.format(resultName,mat,AutoIrrigationFolder[irri])# climateScenario/maturityGroup/irrigation
                            parameter = paramfolderTmpl.format(mat)
                            createLine(outfiles[resultID], project, WeatherRootFolder, wfolder, sid, fcode, fileExtension, plotNr, altitude, Lat, soil_ref, AutoIrrigation[irri], co2, parameter, resultout)
        
    for resultID in range(len(outfiles)) : 
        outfiles[resultID].Close()



def createLine(outSoilfile,proj, wroot, wfolder, sid, fcode, fileExt, plotNr, altitude, Lat, poligonID, irri, CO2concentration, parameter, resultfolder) :
    newline = batchLine.format(proj, wroot, wfolder, sid, fcode, fileExt, plotNr, altitude, Lat, poligonID, irri, CO2concentration, parameter, resultfolder)
    outSoilfile.writelines(newline)


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
    writeBatchFile()
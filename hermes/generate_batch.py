#!/usr/bin/python
# -*- coding: UTF-8

import sys

project="soyeu" 
#WeatherFolder=["0/0_0", "2/GFDL-CM3_45", "2/GISS-E2-R_45","2/HadGEM2-ES_45","2/MIROC5_45","2/MPI-ESM-MR_45"]
WeatherFolder=["2/GFDL-CM3_85", "2/GISS-E2-R_85","2/HadGEM2-ES_85","2/MIROC5_85","2/MPI-ESM-MR_85"]
plotNrs=["10001", "10002"]
AutoIrrigation=["1","0"] 
AutoIrrigationFolder=["Ir","noIr"]
#resultfolder=["0_0_0", "2_GFDL-CM3_45", "2_GISS-E2-R_45","2_HadGEM2-ES_45","2_MIROC5_45","2_MPI-ESM-MR_45"]
resultfolder=["2_GFDL-CM3_85", "2_GISS-E2-R_85","2_HadGEM2-ES_85","2_MIROC5_85","2_MPI-ESM-MR_85"]
maturityGroup = ["0", "00","000","0000","i","ii", "iii"]
paramfolderTmpl="./parameter_{0}"
resultfolderTemplate = "{0}/{1}/{2}/RESULT" # climateScenario/irrigation/maturityGroup/
#CO2concentration=["360","499","499","499","499","499"]
CO2concentration=["571","571","571","571","571"]
batchLine = "project={0} WeatherFolder={1} soilId={2} fcode={3} plotNr={4} Altitude={5} Latitude={6} poligonID={7} AutoIrrigation={8} CO2concentration={9} parameter={10} resultfolder={11}\n"


gridFile = "../stu_eu_layer_grid.csv"
pathOutBatchFile = "./soyeu_{0}_{1}_{2}_batch.txt" 
pathoutLookupFile = "./stu_eu_hermes_batch_lookup.csv"


def writeBatchFile() :
    
    matGroup = "all"
    region = ""
    lat_up = 45.720844
    lon_up = 7.017513
    lat_down = 44.299458
    lon_down = 12.268346

    if len(sys.argv) > 1 and __name__ == "__main__":
        for arg in sys.argv[1:]:
            k, v = arg.split("=")
            if k == "mat":
                matGroup = v
            if k == "region":
                region = v
            if k == "lat_up":
                lat_up = float(v)
            if k == "lon_up":
                lon_up = float(v)
            if k == "lat_down":
                lat_down = float(v)
            if k == "lon_down":
                lon_down = float(v)

    outSet = set()
    if len(region) > 0 :
        outSet = findAllSoilRef(gridFile, (lat_up, lon_up), (lat_down, lon_down)) 

    outfiles = [""] * len(resultfolder)
    for resultID in range(len(resultfolder)) : 
        resultName = resultfolder[resultID]   
        outfiles[resultID] = open(pathOutBatchFile.format(matGroup, resultName, region), mode="wt", newline="")    

    with open(pathoutLookupFile) as sourcefile:
        firstLine = True
        header = dict()
        for line in sourcefile:
            if firstLine :
                firstLine = False
                header = ReadSoilHeader(line)
                continue
            out = loadSoilLine(line)
            soil_ref = out[header["soil_ref"]]
            sid = out[header["sid"]]
            fcode = out[header["fcode"]]
            Lat = out[header["latitude"]]
            altitude = out[header["altitude"]]
            
            for resultID in range(len(resultfolder)) : 
                wfolder = WeatherFolder[resultID]
                co2 = CO2concentration[resultID]
                resultName = resultfolder[resultID]  
                for plotNr in plotNrs :
                    for irri in range(len(AutoIrrigation)) :
                        for mat in maturityGroup :
                            if matGroup == "all" or matGroup == mat : 
                                resultout = resultfolderTemplate.format(resultName,AutoIrrigationFolder[irri],mat)# climateScenario/irrigation/maturityGroup
                                parameter = paramfolderTmpl.format(mat)
                                if len(outSet) == 0 or soil_ref in outSet :
                                    createLine(outfiles[resultID], project, wfolder, sid, fcode, plotNr, altitude, Lat, soil_ref, AutoIrrigation[irri], co2, parameter, resultout)
        
    for resultID in range(len(outfiles)) : 
        outfiles[resultID].close()



def createLine(outSoilfile,proj, wfolder, sid, fcode, plotNr, altitude, Lat, poligonID, irri, CO2concentration, parameter, resultfolder) :
    newline = batchLine.format(proj, wfolder, sid, fcode, plotNr, altitude, Lat, poligonID, irri, CO2concentration, parameter, resultfolder)
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


def findAllSoilRef(gridFile, lat_lon_up, lat_lon_down) :
    outSet = set()
    with open(gridFile) as sourcefile:
        #Column_,Row,Grid_Code,Location,elevation,latitude,longitude,soil_ref
        firstLine = True
        header = dict()
        for line in sourcefile:
            if firstLine :
                firstLine = False
                header = ReadSoilHeader(line)
                continue

            out = loadSoilLine(line)
            latitude = float(out[header["latitude"]])
            longitude = float(out[header["longitude"]])
            soil_ref = out[header["soil_ref"]]

            if latitude <= lat_lon_up[0] and latitude >= lat_lon_down[0] and longitude >= lat_lon_up[1] and longitude <= lat_lon_down[1] :
                outSet.add(soil_ref)
    return outSet


if __name__ == "__main__":
    writeBatchFile()
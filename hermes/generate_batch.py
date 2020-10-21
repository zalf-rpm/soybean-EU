

#!/usr/bin/python
# -*- coding: UTF-8

project="soyeu" 
WeatherFolder=["0/0_0", "2/GFDL-CM3_45", "2/GISS-E2-R_45","2/HadGEM2-ES_45","2/MIROC5_45","2/MPI-ESM-MR_45"]
plotNrs=["10001", "10002"]
AutoIrrigation=["1","0"] 
AutoIrrigationFolder=["Ir","noIr"]
resultfolder=["0_0_0", "2_GFDL-CM3_45", "2_GISS-E2-R_45","2_HadGEM2-ES_45","2_MIROC5_45","2_MPI-ESM-MR_45"]
maturityGroup = ["0", "00","000","0000","i","ii"]
paramfolderTmpl="./parameter_{0}"
resultfolderTemplate = "{0}/{1}/{2}/RESULT" # climateScenario/irrigation/maturityGroup/
CO2concentration=["360","499","499","499","499","499"]
batchLine = "project={0} WeatherFolder={1} soilId={2} fcode={3} plotNr={4} Altitude={5} Latitude={6} poligonID={7} AutoIrrigation={8} CO2concentration={9} parameter={10} resultfolder={11}\n"


pathOutBatchFile = "./soyeu_all_{0}_batch.txt" 
pathoutLookupFile = "./stu_eu_hermes_batch_lookup.csv"

def writeBatchFile() :
    
    outfiles = [""] * len(resultfolder)
    for resultID in range(len(resultfolder)) : 
        resultName = resultfolder[resultID]   
        outfiles[resultID] = open(pathOutBatchFile.format(resultName), mode="wt", newline="")    

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
                            resultout = resultfolderTemplate.format(resultName,AutoIrrigationFolder[irri],mat)# climateScenario/irrigation/maturityGroup
                            parameter = paramfolderTmpl.format(mat)
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

if __name__ == "__main__":
    writeBatchFile()
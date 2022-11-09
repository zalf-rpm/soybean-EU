#!/usr/bin/python
# -*- coding: UTF-8

import gzip
from dataclasses import dataclass
import os
import numpy as np
import math
import sys

def build() :
    "main"

    asciiYieldfutuT1 = "./extract_stats/{0}/dev_max_yield_future_trnoT1.asc.gz"
    asciiYieldfutuT2 = "./extract_stats/{0}/dev_max_yield_future_trnoT2.asc.gz"
    asciiYieldhistT1 = "./extract_stats/{0}/dev_max_yield_historical_trnoT1.asc.gz"
    asciiYieldhistT2 = "./extract_stats/{0}/dev_max_yield_historical_trnoT2.asc.gz"
    irrigatedArea = "./extract_stats/{0}/irrgated_areas.asc.gz"
    cropland_mask = "./extract_stats/{0}/crop_land_mask_historical.asc.gz"

    # asciiAllRisksHistorical = "./extract_stats/{0}/dev_allRisks_historical.asc.gz"
    # asciiAllRisksFuture = "./extract_stats/{0}/dev_allRisks_future.asc.gz"
    asciiAllRisksHistorical = "./extract_stats/{0}/dev_allRisks_5_historical.asc.gz"
    asciiAllRisksFuture = "./extract_stats/{0}/dev_allRisks_5_future.asc.gz"

    asciiAllStdHistorical = "./extract_stats/{0}/all_historical_stdDev.asc.gz"
    asciiAllStdFuture = "./extract_stats/{0}/all_future_stdDev.asc.gz"

    asciiClimAvgModelStdFuture = "./extract_stats/{0}/avg_over_models_stdDev.asc.gz"
    asciiModelAvgClimStdFuture = "./extract_stats/{0}/avg_over_climScen_stdDev.asc.gz"

    asciiSowDiff = "./extract_stats/{0}/dev_sowing_dif_historical_future.asc.gz"

    asciiCompareMGYieldFutT1 = "./extract_stats/{0}/dev_compare_mg_yield_future_trnoT1.asc.gz"
    asciiCompareMGYieldFutT2 = "./extract_stats/{0}/dev_compare_mg_yield_future_trnoT2.asc.gz"

    folder = "eval4.5"
    if len(sys.argv) > 1 and __name__ == "__main__":
        for arg in sys.argv[1:]:
            k, v = arg.split("=")
            if k == "folder":
                folder = v
    
    def readFile(file) :
        print("File:", file)
        header = readAsciiHeader(file)
        ascii_data_array = np.loadtxt(header.ascii_path, dtype=float, skiprows=6)
        # Set the nodata values to nan
        ascii_data_array[ascii_data_array == header.ascii_nodata] = np.nan
        #print(file)
        #print("area:", np.count_nonzero(~np.isnan(ascii_data_array)), "(1x1km pixel)")
        ascii_data_array[ascii_data_array == 0] = np.nan
        #print("evaluated area:", np.count_nonzero(~np.isnan(ascii_data_array)), "(1x1km pixel)")
        return ascii_data_array

    arrAllRisksHistorical = readFile(asciiAllRisksHistorical.format(folder))
    arrAllRisksFuture = readFile(asciiAllRisksFuture.format(folder))
    arrYieldfutuT1 = readFile(asciiYieldfutuT1.format(folder))
    arrYieldfutuT2 = readFile(asciiYieldfutuT2.format(folder))
    arrYieldhistT1 = readFile(asciiYieldhistT1.format(folder))
    arrYieldhistT2 = readFile(asciiYieldhistT2.format(folder))
    irrigated = readFile(irrigatedArea.format(folder))
    cropland = readFile(cropland_mask.format(folder))

    allstdHist = readFile(asciiAllStdHistorical.format(folder))
    allstdFuture = readFile(asciiAllStdFuture.format(folder))
    stdClimAvgModelFuture = readFile(asciiClimAvgModelStdFuture.format(folder))
    stdModelAvgClimFuture = readFile(asciiModelAvgClimStdFuture.format(folder))
    sowDiff = readFile(asciiSowDiff.format(folder))

    arrCompareMGYieldFutT1 = readFile(asciiCompareMGYieldFutT1.format(folder))
    arrCompareMGYieldFutT2 = readFile(asciiCompareMGYieldFutT2.format(folder))

# # for visualization
#     print("max:")
#     print("future T1:", np.nanmax(arrYieldfutuT1))
#     print("future T2:", np.nanmax(arrYieldfutuT2))
#     print("hist T1:", np.nanmax(arrYieldhistT1))
#     print("hist T2:", np.nanmax(arrYieldhistT2))
 

 # 1) Durchschnittlicher Ertrag pro Hektar, einem für die beregneten, einmal für die unberegneten und einmal für alle Soja-Flächen. 
 # AVG max yield - irrigated/rainfed historical - future

    # avgYieldfutuT1 = np.nanmean(arrYieldfutuT1)
    # avgYieldfutuT2 = np.nanmean(arrYieldfutuT2)
    # avgYieldhistT1 = np.nanmean(arrYieldhistT1)
    # avgYieldhistT2 = np.nanmean(arrYieldhistT2)

    # avgYieldfuture = np.nanmean(np.concatenate((arrYieldfutuT1, arrYieldfutuT2), axis=None))
    # avgYieldhistorcal = np.nanmean(np.concatenate((arrYieldhistT1, arrYieldhistT2), axis=None))

# MICRA
    # create a mask 
    def maskedArrayIrrigated(arr, irrigated) :
        numrows = len(arr)    
        numcols = len(arr[0])
        resultArray = np.full((numrows, numcols), np.nan)
        for r in range(numrows) :
            for c in range(numcols) :
                if not math.isnan(arr[r][c]) and not math.isnan(irrigated[r][c]):
                    resultArray[r][c] = arr[r][c]
        return resultArray

    def maskedArrayRainfed(arr, irrigated) :
        numrows = len(arr)    
        numcols = len(arr[0])
        resultArray = np.full((numrows, numcols), np.nan)
        for r in range(numrows) :
            for c in range(numcols) :
                if not math.isnan(arr[r][c]) and math.isnan(irrigated[r][c]):
                    resultArray[r][c] = arr[r][c]
        return resultArray

    def maskedArrayCropland(arr, cropland) : 
        numrows = len(arr)    
        numcols = len(arr[0])
        resultArray = np.full((numrows, numcols), np.nan)
        for r in range(numrows) :
            for c in range(numcols) :
                if not math.isnan(arr[r][c]) and not math.isnan(cropland[r][c]):
                    resultArray[r][c] = arr[r][c] * (cropland[r][c]/100)
        return resultArray

    def maskedNanMeanCropland(arr, cropland) : 
        numrows = len(arr)    
        numcols = len(arr[0])
        sumW    = 0
        sumB    = 0
        for r in range(numrows) :
            for c in range(numcols) :
                if not math.isnan(arr[r][c]) and not math.isnan(cropland[r][c]):
                    sumW = sumW + cropland[r][c]
                    sumB = sumB + (arr[r][c] * cropland[r][c])
        return sumB/sumW

    def maskedNanMeanCroplandConcat(arr, arr2, cropland) : 
        numrows = len(arr)    
        numcols = len(arr[0])
        sumW    = 0
        sumB    = 0
        for r in range(numrows) :
            for c in range(numcols) :
                if not math.isnan(arr[r][c]) and not math.isnan(cropland[r][c]):
                    sumW = sumW + cropland[r][c]
                    sumB = sumB + (arr[r][c] * cropland[r][c])
        for r in range(numrows) :
            for c in range(numcols) :
                if not math.isnan(arr2[r][c]) and not math.isnan(cropland[r][c]):
                    sumW = sumW + cropland[r][c]
                    sumB = sumB + (arr2[r][c] * cropland[r][c])

        return sumB/sumW
    
 
    irrigatedFuture = maskedArrayIrrigated(arrYieldfutuT2, irrigated)
    irrigatedhistorical = maskedArrayIrrigated(arrYieldhistT2, irrigated)
    rainfedFuture = maskedArrayRainfed(arrYieldfutuT1, irrigated)
    rainfedhistorical = maskedArrayRainfed(arrYieldhistT1, irrigated)    
    
    rainfedCompareFuture = maskedArrayRainfed(arrCompareMGYieldFutT1, irrigated)
    irrigatedCompareFuture = maskedArrayIrrigated(arrCompareMGYieldFutT2, irrigated)

    avgYieldirrigatedFuture = np.nanmean(irrigatedFuture)
    avgYieldirrigatedhistorical = np.nanmean(irrigatedhistorical)
    avgYieldrainfedFuture = np.nanmean(rainfedFuture)
    avgYieldrainfedhistorical = np.nanmean(rainfedhistorical)

    avgYieldCroplandIrrigatedFuture = maskedNanMeanCropland(irrigatedFuture,cropland)
    avgYieldCroplandIrrigatedhistorical = maskedNanMeanCropland(irrigatedhistorical,cropland)
    avgYieldCroplandRainfedFuture = maskedNanMeanCropland(rainfedFuture,cropland)
    avgYieldCroplandRainfedhistorical = maskedNanMeanCropland(rainfedhistorical,cropland)

    avgYieldfutureMasked = np.nanmean(np.concatenate((irrigatedFuture, rainfedFuture), axis=None))
    avgYieldhistorcalMasked = np.nanmean(np.concatenate((irrigatedhistorical, rainfedhistorical), axis=None))

    avgYieldCroplandfutureMasked = maskedNanMeanCroplandConcat(irrigatedFuture, rainfedFuture,cropland)
    avgYieldCroplandhistorcalMasked = maskedNanMeanCroplandConcat(irrigatedhistorical, rainfedhistorical,cropland)

    avgIrrigatedCompareFuture = np.nanmean(irrigatedCompareFuture) # irrigated
    avgRainfedCompareFuture = np.nanmean(rainfedCompareFuture) # rainfed 
    avgCompareFutureMasked = np.nanmean(np.concatenate((avgIrrigatedCompareFuture, avgRainfedCompareFuture), axis=None)) #Total

    avgCroplandIrrigatedCompareFuture = maskedNanMeanCropland(irrigatedCompareFuture,cropland) # irrigated
    avgCroplandRainfedCompareFuture = maskedNanMeanCropland(rainfedCompareFuture,cropland) # rainfed 
    avgCroplandCompareFutureMasked = np.nanmean(np.concatenate((avgCroplandIrrigatedCompareFuture, avgCroplandRainfedCompareFuture), axis=None)) #Total



 # 2) Die Soja-Fläche in der Baseline und die Soja-Fläche in der Zukunft 
 # Area historical - future (irr/rainfed)

    # areaYieldfutuT1 = np.count_nonzero(~np.isnan(arrYieldfutuT1))
    # areaYieldfutuT2 = np.count_nonzero(~np.isnan(arrYieldfutuT2))
    # areaYieldhistT1 = np.count_nonzero(~np.isnan(arrYieldhistT1))
    # areaYieldhistT2 = np.count_nonzero(~np.isnan(arrYieldhistT2))

    areaYieldirrgatedFuture = np.count_nonzero(~np.isnan(irrigatedFuture))
    areaYieldirrgatedhistorical = np.count_nonzero(~np.isnan(irrigatedhistorical))
    areaYieldrainfedFuture = np.count_nonzero(~np.isnan(rainfedFuture))
    areaYieldrainfedhistorical = np.count_nonzero(~np.isnan(rainfedhistorical))

    areaYieldirrgatedFutureMasked = np.nansum(maskedArrayCropland(~np.isnan(irrigatedFuture),cropland))
    areaYieldirrgatedhistoricalMasked = np.nansum(maskedArrayCropland(~np.isnan(irrigatedhistorical),cropland))
    areaYieldrainfedFutureMasked = np.nansum(maskedArrayCropland(~np.isnan(rainfedFuture),cropland))
    areaYieldrainfedhistoricalMasked = np.nansum(maskedArrayCropland(~np.isnan(rainfedhistorical),cropland))


 # 3) den durchschnittlichen Ertrag pro Fläche auf den Soja-Flächen der Baseline im Vergleich mit genau diesen Flächen in der Zukunft (flächentreu) und den durchschnittlichen Ertrag pro Fläche auf den Flächen die in der Zukunft neu hinzugekommen sind.
    
    def avgIntersection(future, historical) :
        numrows = len(historical)    
        numcols = len(historical[0])
        counter = 0
        sum = 0
        
        for r in range(numrows) :
            for c in range(numcols) :
                if not math.isnan(historical[r][c]):
                    counter += 1
                    if not math.isnan(future[r][c]) :
                        sum += future[r][c]
        avg = 0
        if counter > 0 :
            avg = sum / counter
        return avg

    # areaYieldT1 = avgIntersection(arrYieldfutuT1, arrYieldhistT1)
    # areaYieldT2 = avgIntersection(arrYieldfutuT2, arrYieldhistT2)

    areaYieldirrigated = avgIntersection(irrigatedFuture,irrigatedhistorical)
    areaYieldrainfed = avgIntersection(rainfedFuture, rainfedhistorical)

    def avgIntersectionOuter(future, historical) :
        numrows = len(historical)    # 3 rows in your example
        numcols = len(historical[0])
        counter = 0
        sum = 0
        for r in range(numrows) :
            for c in range(numcols) :
                if not math.isnan(future[r][c]) and math.isnan(historical[r][c]):
                    counter += 1
                    sum += future[r][c]
        avg = 0
        if counter > 0 :
            avg = sum / counter
        return avg

    # areaYieldAddT1 = avgIntersectionOuter(arrYieldfutuT1, arrYieldhistT1)
    # areaYieldAddT2 = avgIntersectionOuter(arrYieldfutuT2, arrYieldhistT2)

    areaYieldAddirrigated = avgIntersectionOuter(irrigatedFuture,irrigatedhistorical)
    areaYieldAddrainfed = avgIntersectionOuter(rainfedFuture, rainfedhistorical)


    
    # Ich benötige die absoluten Flächen unter den jeweiligen Risiko-Faktoren in km². 
    # Dabei soll es keine Rolle spielen, ob auf einem Pixel auch noch andere Risiko-Faktoren wirken. 
    # D.h. die Summe der vier Zahlen ist dann größer als die gesamte Soja-Fläche.

    arrAllRisksHistorical[arrAllRisksHistorical == np.nan] = 0
    arrAllRisksFuture[arrAllRisksFuture == np.nan] = 0

    arrAllRisksHistorical = arrAllRisksHistorical.flatten()
    arrAllRisksFuture = arrAllRisksFuture.flatten()
    arrAllRisksHistorical = arrAllRisksHistorical.astype('int')
    arrAllRisksFuture = arrAllRisksFuture.astype('int')

    # bit mask
	# 1  shortSeason
	# 2  coldspell
	#    shortSeason + coldspell
	# 4  drought risk
	#    drought risk + shortSeason
	#    drought risk + coldspell
	#    drought risk + shortSeason + coldspell
	# 8  heat stress
    #    heat stress + shortSeason
    #    heat stress + coldspell
    #    heat stress + shortSeason + coldspell
    #    heat stress + drought risk
    #    heat stress + drought risk + shortSeason
    #    heat stress + drought risk + coldspell
    #    heat stress + drought risk + shortSeason + coldspell
    # 16 harvest rain
	#    harvest rain + shortSeason
	#    harvest rain + coldspell
	#    harvest rain + shortSeason + coldspell
	#    harvest rain + drought risk
	#    harvest rain + shortSeason + drought risk
	#    harvest rain + coldspell + drought risk
	#    harvest rain + shortSeason + coldspell + drought risk
	
    valShortSeasonRisksHistorical = np.count_nonzero(((arrAllRisksHistorical & 1) > 0))
    valShortSeasonRisksFuture = np.count_nonzero(((arrAllRisksFuture & 1) > 0))
    valColdSpellRisksHistorical = np.count_nonzero(((arrAllRisksHistorical & 2) > 0))
    valColdSpellRisksFuture = np.count_nonzero(((arrAllRisksFuture & 2) > 0))
    valDroughtRisksHistorical = np.count_nonzero(((arrAllRisksHistorical & 4) > 0))
    valDroughtRisksFuture = np.count_nonzero(((arrAllRisksFuture & 4) > 0))
    valHeatRisksHistorical = np.count_nonzero(((arrAllRisksHistorical & 8) > 0))
    valHeatRisksFuture = np.count_nonzero(((arrAllRisksFuture & 8) > 0))
    valHarvestRainRisksHistorical = np.count_nonzero(((arrAllRisksHistorical & 16) > 0))
    valHarvestRainRisksFuture = np.count_nonzero(((arrAllRisksFuture & 16) > 0))

# std deviation historic and future
    avgAllStdDevFuture = np.nanmean(allstdFuture)
    avgAllStdDevhistorical = np.nanmean(allstdHist)
    avgstdClimAvgModelFuture = np.nanmean(stdClimAvgModelFuture)
    avgstdModelAvgClimFuture = np.nanmean(stdModelAvgClimFuture)

# sow diff 
    avgSowDiff = np.nanmean(sowDiff)


    # print("Average Yield future T1:    ",  int(avgYieldfutuT1), "[t ha-1]")
    # print("Average Yield future T2:    ",  int(avgYieldfutuT2), "[t ha-1]")
    # print("Average Yield historical T1:",  int(avgYieldhistT1), "[t ha-1]")
    # print("Average Yield historical T2:",  int(avgYieldhistT2), "[t ha-1]")

    # print("Average Yield future:       ", int(avgYieldfuture), "[t ha-1]")
    # print("Average Yield historical:   ", int(avgYieldhistorcal), "[t ha-1]")

    # print("micra: ")

    print("----------Avg. Yields--------------- ")
    print("Average Yield future irrig:   ", int(avgYieldirrigatedFuture), "[t ha-1]")
    print("Average Yield future rainfed: ", int(avgYieldrainfedFuture), "[t ha-1]")
    print("Average Yield hist. irrig:    ", int(avgYieldirrigatedhistorical), "[t ha-1]")
    print("Average Yield hist. rainfed:  ", int(avgYieldrainfedhistorical), "[t ha-1]")

    print("Average Yield future     :    ", int(avgYieldfutureMasked), "[t ha-1]")
    print("Average Yield historical :    ", int(avgYieldhistorcalMasked), "[t ha-1]")

    print("----------Apply Cropland mask--------------- ")

    print("Average Yield in Cropland future irrig:   ", int(avgYieldCroplandIrrigatedFuture), "[t ha-1]")
    print("Average Yield in Cropland future rainfed: ", int(avgYieldCroplandRainfedFuture), "[t ha-1]")
    print("Average Yield in Cropland hist. irrig:    ", int(avgYieldCroplandIrrigatedhistorical), "[t ha-1]")
    print("Average Yield in Cropland hist. rainfed:  ", int(avgYieldCroplandRainfedhistorical), "[t ha-1]")

    print("Average Yield in Cropland future     :    ", int(avgYieldCroplandfutureMasked), "[t ha-1]")
    print("Average Yield in Cropland historical :    ", int(avgYieldCroplandhistorcalMasked), "[t ha-1]")


    print(" --------- compare yields------------------------ ")

    print("Average productivity hist. MG in Future - irrigated: ",int(avgIrrigatedCompareFuture), "[t ha-1]")
    print("Average productivity hist. MG in Future - rainfed:   ",int(avgRainfedCompareFuture), "[t ha-1]")
    print("Average productivity hist. MG in Future - total:     ",int(avgCompareFutureMasked), "[t ha-1]")

    print("Average productivity diff (future-hist) irrigated: ",int(avgIrrigatedCompareFuture - avgYieldirrigatedhistorical), "[t ha-1]")
    print("Average productivity diff (future-hist) rainfed:   ",int(avgRainfedCompareFuture - avgYieldrainfedhistorical), "[t ha-1]")
    print("Average productivity diff (future-hist) total:     ",int(avgCompareFutureMasked -avgYieldhistorcalMasked), "[t ha-1]")
    
    print("----------Apply Cropland mask-------------- ")

    print("Average productivity in Cropland hist. MG in Future - irrigated: ",int(avgCroplandIrrigatedCompareFuture), "[t ha-1]")
    print("Average productivity in Cropland hist. MG in Future - rainfed:   ",int(avgCroplandRainfedCompareFuture), "[t ha-1]")
    print("Average productivity in Cropland hist. MG in Future - total:     ",int(avgCroplandCompareFutureMasked), "[t ha-1]")

    print("Average productivity in Cropland diff (future-hist) irrigated:   ",int(avgCroplandIrrigatedCompareFuture - avgYieldCroplandIrrigatedhistorical), "[t ha-1]")
    print("Average productivity in Cropland diff (future-hist) rainfed:     ",int(avgCroplandRainfedCompareFuture - avgYieldCroplandRainfedhistorical), "[t ha-1]")
    print("Average productivity in Cropland diff (future-hist) total:       ",int(avgCroplandCompareFutureMasked - avgYieldCroplandhistorcalMasked), "[t ha-1]")

    print("------------------------------------------- ")
    # print("Soybean Area future T1:     " ,areaYieldfutuT1,"(1x1km pixel)")
    # print("Soybean Area future T2:     " ,areaYieldfutuT2,"(1x1km pixel)")
    # print("Soybean Area historical T1: ", areaYieldhistT1, "(1x1km pixel)")
    # print("Soybean Area historical T2: ", areaYieldhistT2, "(1x1km pixel)")

    # print("Note: the irrigated area has not changed much, because we are using the same micra mask")
    print("-------------Soybean areas in 1x1km pixel ------------------------------ ")
    print("Soybean Area irrgated future:     ", areaYieldirrgatedFuture, "(1x1km pixel)")
    print("Soybean Area irrgated historical: ", areaYieldirrgatedhistorical, "(1x1km pixel)")
    print("Soybean Area rainfed future:      ", areaYieldrainfedFuture, "(1x1km pixel)")
    print("Soybean Area rainfed historical:  ", areaYieldrainfedhistorical, "(1x1km pixel)")

    print("Soybean Area All future:  ", areaYieldrainfedFuture + areaYieldirrgatedFuture, "(1x1km pixel)")
    print("Soybean Area All historical:  ", areaYieldrainfedhistorical + areaYieldirrgatedhistorical, "(1x1km pixel)")    

    #print("Soybean Area Mask rainfed future:     ", areaYieldfutureMasked, "(1x1km pixel)")
    print("-----------Apply Cropland mask-------------------------------- ")
    print("Soybean Cropland Area irrgated future:     ", int(areaYieldirrgatedFutureMasked), "(1x1km pixel)")
    print("Soybean Cropland Area irrgated historical: ", int(areaYieldirrgatedhistoricalMasked), "(1x1km pixel)")
    print("Soybean Cropland Area rainfed future:      ", int(areaYieldrainfedFutureMasked), "(1x1km pixel)")
    print("Soybean Cropland Area rainfed historical: ", int(areaYieldrainfedhistoricalMasked), "(1x1km pixel)")

    print("Soybean Cropland Area All future:  ", int(areaYieldirrgatedFutureMasked + areaYieldrainfedFutureMasked), "(1x1km pixel)")
    print("Soybean Cropland Area All historical:  ", int(areaYieldirrgatedhistoricalMasked + areaYieldrainfedhistoricalMasked), "(1x1km pixel)")   

    # print("Future Yield on baseline T1:", int(areaYieldT1), "[t ha-1]")
    # print("Future Yield on baseline T2:", int(areaYieldT2), "[t ha-1]")
    # print("Future Yield addition T1:   ", int(areaYieldAddT1), "[t ha-1]")
    # print("Future Yield addition T2:   ", int(areaYieldAddT2), "[t ha-1]")
    print("---------Area Yield---------------------------------- ")

    print("Future Yield on baseline irrigated :", int(areaYieldirrigated), "[t ha-1]")
    print("Future Yield on baseline rainfed:   ", int(areaYieldrainfed), "[t ha-1]")
    print("Future Yield addition irrigated:    ", int(areaYieldAddirrigated), "[t ha-1]")
    print("Future Yield addition rainfed:      ", int(areaYieldAddrainfed), "[t ha-1]")

    print("---------Risk Factors ---------------------------------- ")
    print("Soybean Area Short Season historical: ",valShortSeasonRisksHistorical, "(1x1km pixel)")
    print("Soybean Area Short Season future:     ",valShortSeasonRisksFuture, "(1x1km pixel)")
    print("Soybean Area Cold Spell historical:   ",valColdSpellRisksHistorical, "(1x1km pixel)")
    print("Soybean Area Cold Spell future:       ",valColdSpellRisksFuture, "(1x1km pixel)")
    print("Soybean Area Drought historical:      ",valDroughtRisksHistorical, "(1x1km pixel)")
    print("Soybean Area Drought future:          ",valDroughtRisksFuture, "(1x1km pixel)")
    print("Soybean Area Heat Stress historical:   ",valHeatRisksHistorical, "(1x1km pixel)")
    print("Soybean Area Heat Stress future:       ",valHeatRisksFuture, "(1x1km pixel)")
    print("Soybean Area Harvest Rain historical: ",valHarvestRainRisksHistorical, "(1x1km pixel)")
    print("Soybean Area Harvest Rain future:     ",valHarvestRainRisksFuture, "(1x1km pixel)")

    print("---------Std. Deviation  ---------------------------------- ")
    print("Standart deviation all historical: ", int(avgAllStdDevhistorical))
    print("Standart deviation all future:     ", int(avgAllStdDevFuture))
    
    print("Standart deviation Climate avg over Model: ", int(avgstdClimAvgModelFuture))
    print("Standart deviation Model avg Climate:      ", int(avgstdModelAvgClimFuture))

    print("---------Sowing Difference  ---------------------------------- ")
    print("Average Sowing Diffenence :      ", int(avgSowDiff), "(days)")

@dataclass
class AsciiHeader:
    ascii_path: str
    ascci_cols: int
    ascii_rows: int
    ascii_xll: float
    ascii_yll: float
    ascii_cs: float
    ascii_nodata: float
    image_extent: list

def readAsciiHeader(ascii_path) :
    if ascii_path.endswith(".gz") :
           # Read in ascii header data
        with gzip.open(ascii_path, 'rt') as source:
            ascii_header = source.readlines()[:6] 
    else :
        # Read in ascii header data
        with open(ascii_path, 'r') as source:
            ascii_header = source.readlines()[:6]

    # Read the ASCII raster header
    ascii_header = [item.strip().split()[-1] for item in ascii_header]
    ascci_cols = int(ascii_header[0])
    ascii_rows = int(ascii_header[1])
    ascii_xll = float(ascii_header[2])
    ascii_yll = float(ascii_header[3])
    ascii_cs = float(ascii_header[4])
    ascii_nodata = float(ascii_header[5])

    image_extent = [
                ascii_xll, ascii_xll + ascci_cols * ascii_cs,
                ascii_yll, ascii_yll + ascii_rows * ascii_cs] 

    return AsciiHeader(ascii_path, ascci_cols, ascii_rows, ascii_xll, ascii_yll, ascii_cs, ascii_nodata, image_extent)


if __name__ == "__main__":
    build()
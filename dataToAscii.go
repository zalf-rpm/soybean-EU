package main

import (
	"bufio"
	"compress/gzip"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/cheggaaa/pb"
	"gonum.org/v1/gonum/stat"
)

const asciiOutFilenameAvg = "avg_%s_trno%s.asc"                             // mGroup_treatmentnumber
const asciiOutFilenameDeviAvg = "devi_avg_%s_trno%s.asc"                    // mGroup_treatmentnumber
const asciiOutFilenameMaxYield = "maxyield_trno%s.asc"                      // treatmentnumber
const asciiOutFilenameMaxYieldMat = "maxyield_matgroup_trno%s.asc"          // treatmentnumber
const asciiOutFilenameMaxYieldDevi = "maxyield_Devi_trno%s.asc"             // treatmentnumber
const asciiOutFilenameMaxYieldMatDevi = "maxyield_Devi_matgroup_trno%s.asc" // treatmentnumber
const asciiOutFilenameWaterDiff = "water_Diff_%s.asc"
const asciiOutFilenameWaterDiffMax = "water_Diff_max_yield.asc"
const asciiOutFilenameSowDoy = "doy_sow_%s_trno%s.asc"                        // mGroup_treatmentnumber
const asciiOutFilenameEmergeDoy = "doy_emg_%s_trno%s.asc"                     // mGroup_treatmentnumber
const asciiOutFilenameAnthesisDoy = "doy_ant_%s_trno%s.asc"                   // mGroup_treatmentnumber
const asciiOutFilenameMatDoy = "doy_mat_%s_trno%s.asc"                        // mGroup_treatmentnumber
const asciiOutFilenameCoolWeather = "coolweather_%s_trno%s.asc"               // mGroup_treatmentnumber
const asciiOutFilenameCoolWeatherDeath = "coolweather_severity_%s_trno%s.asc" // mGroup_treatmentnumber
const asciiOutFilenameCoolWeatherWeight = "coolweather_weights_%s_trno%s.asc" // mGroup_treatmentnumber
const asciiOutFilenameWetHarvest = "harvest_wet_%s_trno%s.asc"                // mGroup_treatmentnumber
const asciiOutFilenameLateHarvest = "harvest_late_%s_trno%s.asc"              // mGroup_treatmentnumber
const asciiOutFilenameMatIsHarvest = "harvest_before_maturity_%s_trno%s.asc"  // mGroup_treatmentnumber

const climateFilePattern = "%s_v3test.csv"

// USER switch for setting
const USER = "local"

// CROPNAME to analyse
const CROPNAME = "soybean"

// NONEVALUE for ascii table
const NONEVALUE = -9999

// SHOWPROGRESSBAR in cmd line
const SHOWPROGRESSBAR = true

func main() {

	// path to files
	PATHS := map[string]map[string]string{
		"local": {
			"projectdatapath": "./",
			"sourcepath":      "./source/",
			"outputpath":      ".",
			"climate-data":    "./climate-data/corrected/", // path to climate data
			"ascii-out":       "asciigrids_debug/",         // path to ascii grids
			"png-out":         "png_debug/",                // path to png images
			"pdf-out":         "pdf-out_debug/",            // path to pdf package
		},
		"test": {
			"projectdatapath": "./",
			"sourcepath":      "./source/",
			"outputpath":      "./testout/",
			"climate-data":    "./climate-data/corrected/", // path to climate data
			"ascii-out":       "asciigrids2/",              // path to ascii grids
			"png-out":         "png2/",                     // path to png images
			"pdf-out":         "pdf-out2/",                 // path to pdf package
		},
		"Cluster": {
			"projectdatapath": "/project/",
			"sourcepath":      "/source/",
			"outputpath":      "/out/",
			"climate-data":    "/climate-data/", // path to climate data
			"ascii-out":       "asciigrid/",     // path to ascii grids
			"png-out":         "png/",           // path to png images
			"pdf-out":         "pdf-out/",       // path to pdf package
		},
	}

	// command line flags
	pathPtr := flag.String("path", USER, "path id")
	sourcePtr := flag.String("source", "", "path to sourece folder")
	outPtr := flag.String("out", "", "path to out folder")
	noprogessPtr := flag.Bool("showprogess", SHOWPROGRESSBAR, "show progress bar")

	flag.Parse()

	pathID := *pathPtr
	showBar := *noprogessPtr
	sourceFolder := *sourcePtr
	outputFolder := *outPtr

	if len(sourceFolder) == 0 {
		sourceFolder = PATHS[pathID]["sourcepath"]
	}
	if len(outputFolder) == 0 {
		outputFolder = PATHS[pathID]["outputpath"]
	}

	climateFolder := PATHS[pathID]["climate-data"]
	asciiOutFolder := filepath.Join(outputFolder, PATHS[pathID]["ascii-out"])
	// pngFolder := filepath.Join(outputFolder, PATHS[pathID]["png-out"])
	// pdfFolder := filepath.Join(outputFolder, PATHS[pathID]["pdf-out"])
	projectpath := filepath.Join(outputFolder, PATHS[pathID]["projectdatapath"])
	gridSource := filepath.Join(projectpath, "stu_eu_layer_grid.csv")
	refSource := filepath.Join(projectpath, "stu_eu_layer_ref.csv")

	extRow, extCol, gridSourceLookup := GetGridLookup(gridSource)

	climateRef := GetClimateReference(refSource)

	filelist, err := ioutil.ReadDir(sourceFolder)
	if err != nil {
		log.Fatal(err)
	}
	maxRefNo := len(filelist) // size of the list
	for _, file := range filelist {
		refIDStr := strings.Split(strings.Split(file.Name(), ".")[0], "_")[3]
		refID64, err := strconv.ParseInt(refIDStr, 10, 64)
		if err != nil {
			log.Fatal(err)
		}
		if maxRefNo < int(refID64) {
			maxRefNo = int(refID64)
		}
	}

	maxAllAvgYield := 0.0
	maxSdtDeviation := 0.0
	numInput := len(filelist)
	currentInput := 0
	allGrids := make(map[SimKeyTuple][]int)
	StdDevAvgGrids := make(map[SimKeyTuple][]int)
	// #matureGrid = dict()
	// #flowerGrid = dict()
	harvestGrid := make(map[SimKeyTuple][]int)
	matIsHavestGrid := make(map[SimKeyTuple][]int)
	lateHarvestGrid := make(map[SimKeyTuple][]int)
	climateFilePeriod := make(map[string]string)
	coolWeatherImpactGrid := make(map[SimKeyTuple][]int)
	coolWeatherDeathGrid := make(map[SimKeyTuple][]int)
	coolWeatherImpactWeightGrid := make(map[SimKeyTuple][]int)
	wetHarvestGrid := make(map[SimKeyTuple][]int)
	sumMaxOccurrence := 0
	sumMaxDeathOccurrence := 0
	maxLateHarvest := 0
	maxWetHarvest := 0
	maxMatHarvest := 0
	sumLowOccurrence := 0
	sumMediumOccurrence := 0
	sumHighOccurrence := 0
	outputGridsGenerated := false
	progessFunc := progress(numInput, "input files")

	// iterate over all model run results
	for _, sourcefileInfo := range filelist {
		sourcefileName := sourcefileInfo.Name()
		sourcefile, err := os.Open(filepath.Join(sourceFolder, sourcefileName))
		if err != nil {
			log.Fatal(err)
		}
		defer sourcefile.Close()
		refIDStr := strings.Split(strings.Split(sourcefileName, ".")[0], "_")[3]
		refID64, err := strconv.ParseInt(refIDStr, 10, 64)
		if err != nil {
			log.Fatal(err)
		}
		refIDIndex := int(refID64) - 1
		simulations := make(map[SimKeyTuple][]float64)
		simDoyFlower := make(map[SimKeyTuple][]int)
		simDoyMature := make(map[SimKeyTuple][]int)
		simDoyHarvest := make(map[SimKeyTuple][]int)
		simMatIsHarvest := make(map[SimKeyTuple][]bool)
		simLastHarvestDate := make(map[SimKeyTuple][]bool)
		dateYearOrder := make(map[SimKeyTuple][]int)
		firstLine := true
		var header SimDataIndex
		scanner := bufio.NewScanner(sourcefile)
		for scanner.Scan() {
			line := scanner.Text()
			if firstLine {
				// read header
				firstLine = false
				header = readHeader(line)
			} else {
				// load relevant line content
				lineKey, lineContent := loadLine(line, header)
				// check for the lines with a specific crop
				if IsCrop(lineKey, CROPNAME) && (lineKey.treatNo == "T1" || lineKey.treatNo == "T2") {
					yieldValue := lineContent.yields
					period := lineContent.period
					yearValue := lineContent.year
					// sowValue = lineContent[-5]
					// emergeValue = lineContent[-4]
					flowerValue := lineContent.antDOY
					matureValue := lineContent.matDOY
					harvestValue := lineContent.harDOY
					if _, ok := simulations[lineKey]; !ok {
						simulations[lineKey] = make([]float64, 0, 30)
						simDoyFlower[lineKey] = make([]int, 0, 30)
						simDoyMature[lineKey] = make([]int, 0, 30)
						simDoyHarvest[lineKey] = make([]int, 0, 30)
						simMatIsHarvest[lineKey] = make([]bool, 0, 30)
						simLastHarvestDate[lineKey] = make([]bool, 0, 30)
						dateYearOrder[lineKey] = make([]int, 0, 30)
					}
					if _, ok := climateFilePeriod[lineKey.climateSenario]; !ok {
						climateFilePeriod[lineKey.climateSenario] = period
					}
					simulations[lineKey] = append(simulations[lineKey], yieldValue)
					simDoyFlower[lineKey] = append(simDoyFlower[lineKey], flowerValue)
					simDoyMature[lineKey] = append(simDoyMature[lineKey], func(matureValue, harvestValue int) int {
						if matureValue > 0 {
							return matureValue
						}
						return harvestValue
					}(matureValue, harvestValue))
					simDoyHarvest[lineKey] = append(simDoyHarvest[lineKey], harvestValue)
					simMatIsHarvest[lineKey] = append(simMatIsHarvest[lineKey], matureValue <= 0 && harvestValue > 0)
					simLastHarvestDate[lineKey] = append(simLastHarvestDate[lineKey], time.Date(yearValue, time.October, 31, 0, 0, 0, 0, time.UTC).YearDay() == harvestValue)
					dateYearOrder[lineKey] = append(dateYearOrder[lineKey], yearValue)
				}
			}
		}
		if !outputGridsGenerated {
			outputGridsGenerated = true
			for simKey := range simulations {
				allGrids[simKey] = newGridLookup(maxRefNo, NONEVALUE)
				StdDevAvgGrids[simKey] = newGridLookup(maxRefNo, NONEVALUE)
				// #matureGrid[simKey] = newGridLookup(maxRefNo, NONEVALUE)
				// #flowerGrid[simKey] = newGridLookup(maxRefNo, NONEVALUE)
				harvestGrid[simKey] = newGridLookup(maxRefNo, NONEVALUE)
				matIsHavestGrid[simKey] = newGridLookup(maxRefNo, NONEVALUE)
				lateHarvestGrid[simKey] = newGridLookup(maxRefNo, NONEVALUE)
				coolWeatherImpactGrid[simKey] = newGridLookup(maxRefNo, NONEVALUE)
				coolWeatherDeathGrid[simKey] = newGridLookup(maxRefNo, NONEVALUE)
				coolWeatherImpactWeightGrid[simKey] = newGridLookup(maxRefNo, NONEVALUE)
				wetHarvestGrid[simKey] = newGridLookup(maxRefNo, NONEVALUE)
			}
		}
		for simKey := range simulations {
			pixelValue := CalculatePixel(simulations[simKey])
			if pixelValue > maxAllAvgYield {
				maxAllAvgYield = pixelValue
			}
			stdDeviation := stat.StdDev(simulations[simKey], nil)
			if stdDeviation > maxSdtDeviation {
				maxSdtDeviation = stdDeviation
			}
			// matureGrid[simKey][currRow-1][currCol-1] = int(average(simDoyMature[simKey]))
			// flowerGrid[simKey][currRow-1][currCol-1] = int(average(simDoyFlower[simKey]))

			harvestGrid[simKey][refIDIndex] = averageInt(simDoyHarvest[simKey])
			sum := 0
			for _, val := range simMatIsHarvest[simKey] {
				if val {
					sum++
				}
			}
			matIsHavestGrid[simKey][refIDIndex] = sum
			sum = 0
			for _, val := range simLastHarvestDate[simKey] {
				if val {
					sum++
				}
			}
			lateHarvestGrid[simKey][refIDIndex] = sum
			allGrids[simKey][refIDIndex] = int(pixelValue)
			StdDevAvgGrids[simKey][refIDIndex] = int(stdDeviation)

			if maxLateHarvest < lateHarvestGrid[simKey][refIDIndex] {
				maxLateHarvest = lateHarvestGrid[simKey][refIDIndex]
			}
			if maxMatHarvest < matIsHavestGrid[simKey][refIDIndex] {
				maxMatHarvest = matIsHavestGrid[simKey][refIDIndex]
			}
		}
		//coolWeatherImpactGrid
		for scenario := range climateFilePeriod {
			climateRowCol := climateRef[refIDIndex]
			climatePath := filepath.Join(climateFolder, climateFilePeriod[scenario], scenario, fmt.Sprintf(climateFilePattern, climateRowCol))
			if _, err := os.Stat(climatePath); err == nil {
				climatefile, err := os.Open(climatePath)
				if err != nil {
					log.Fatal(err)
				}
				defer climatefile.Close()
				firstLines := 0
				numOccurrenceHigh := make(map[SimKeyTuple]int)
				numOccurrenceMedium := make(map[SimKeyTuple]int)
				numOccurrenceLow := make(map[SimKeyTuple]int)
				numWetHarvest := make(map[SimKeyTuple]int)
				var header ClimateHeader
				precipPrevDays := newDataLastDays(5)
				scanner := bufio.NewScanner(climatefile)
				for scanner.Scan() {
					line := scanner.Text()
					if firstLines < 2 {
						// read header
						if firstLines < 1 {
							header = ReadClimateHeader(line)
						}
						firstLines++
					} else {
						// load relevant line content
						lineContent := loadClimateLine(line, header)
						date := lineContent.isodate
						tmin := lineContent.tmin
						precip := lineContent.precip
						precipPrevDays.addDay(precip)
						dateYear := date.Year()
						if tmin < 15 {
							for simKey := range dateYearOrder {
								if simKey.climateSenario == scenario {
									yearIndex := -1
									for i, val := range dateYearOrder[simKey] {
										if val == dateYear {
											yearIndex = i
										}
									}
									if yearIndex == -1 {
										break
									}
									startDOY := simDoyFlower[simKey][yearIndex]
									endDOY := simDoyMature[simKey][yearIndex]
									if IsDateInGrowSeason(startDOY, endDOY, date) {
										if _, ok := numOccurrenceHigh[simKey]; !ok {
											numOccurrenceHigh[simKey] = 0
											numOccurrenceMedium[simKey] = 0
											numOccurrenceLow[simKey] = 0
										}
										if tmin < 8 {
											numOccurrenceHigh[simKey]++
										} else if tmin < 10 {
											numOccurrenceMedium[simKey]++
										} else {
											numOccurrenceLow[simKey]++
										}
									}
									// check if this date is harvest
									harvestDOY := simDoyHarvest[simKey][yearIndex]
									if harvestDOY > 0 && IsDateInGrowSeason(harvestDOY, harvestDOY, date) {
										wasWetHarvest := true
										for _, x := range precipPrevDays.getData() {
											wasWetHarvest = (x > 0) && wasWetHarvest
										}
										if _, ok := numWetHarvest[simKey]; !ok {
											numWetHarvest[simKey] = 0
										}
										if wasWetHarvest {
											numWetHarvest[simKey]++
										}
									}
								}
							}
						}
					}
				}
				for simKey := range simulations {
					if simKey.climateSenario == scenario {
						if allGrids[simKey][refIDIndex] > 0 {
							if _, ok := numOccurrenceMedium[simKey]; ok {
								sumOccurrence := numOccurrenceMedium[simKey] + numOccurrenceHigh[simKey] + numOccurrenceLow[simKey]
								sumDeathOccurrence := numOccurrenceMedium[simKey]*10 + numOccurrenceHigh[simKey]*100 + numOccurrenceLow[simKey]

								if sumLowOccurrence < numOccurrenceLow[simKey] {
									sumLowOccurrence = numOccurrenceLow[simKey]
								}
								if sumMediumOccurrence < numOccurrenceMedium[simKey] {
									sumMediumOccurrence = numOccurrenceMedium[simKey]
								}
								if sumHighOccurrence < numOccurrenceHigh[simKey] {
									sumHighOccurrence = numOccurrenceHigh[simKey]
								}

								weight := 0

								if numOccurrenceHigh[simKey] <= 125 && numOccurrenceHigh[simKey] > 0 {
									weight = 9
								} else if numOccurrenceHigh[simKey] <= 500 && numOccurrenceHigh[simKey] > 0 {
									weight = 10
								} else if numOccurrenceHigh[simKey] <= 1000 && numOccurrenceHigh[simKey] > 0 {
									weight = 11
								} else if numOccurrenceHigh[simKey] > 1000 && numOccurrenceHigh[simKey] > 0 {
									weight = 12
								} else if numOccurrenceMedium[simKey] <= 75 && numOccurrenceMedium[simKey] > 0 {
									weight = 5
								} else if numOccurrenceMedium[simKey] <= 150 && numOccurrenceMedium[simKey] > 0 {
									weight = 6
								} else if numOccurrenceMedium[simKey] <= 300 && numOccurrenceMedium[simKey] > 0 {
									weight = 7
								} else if numOccurrenceMedium[simKey] > 300 && numOccurrenceMedium[simKey] > 0 {
									weight = 8
								} else if numOccurrenceLow[simKey] <= 250 && numOccurrenceLow[simKey] > 0 {
									weight = 1
								} else if numOccurrenceLow[simKey] <= 500 && numOccurrenceLow[simKey] > 0 {
									weight = 2
								} else if numOccurrenceLow[simKey] <= 1000 && numOccurrenceLow[simKey] > 0 {
									weight = 3
								} else if numOccurrenceLow[simKey] > 1000 && numOccurrenceLow[simKey] > 0 {
									weight = 4
								}
								coolWeatherImpactGrid[simKey][refIDIndex] = sumOccurrence
								coolWeatherDeathGrid[simKey][refIDIndex] = sumDeathOccurrence
								coolWeatherImpactWeightGrid[simKey][refIDIndex] = weight
								if sumMaxOccurrence < sumOccurrence {
									sumMaxOccurrence = sumOccurrence
								}
								if sumMaxDeathOccurrence < sumDeathOccurrence {
									sumMaxDeathOccurrence = sumDeathOccurrence
								}
							} else {
								coolWeatherImpactGrid[simKey][refIDIndex] = 0
								coolWeatherDeathGrid[simKey][refIDIndex] = 0
							}
							// wet harvest occurence
							if _, ok := numWetHarvest[simKey]; ok {
								wetHarvestGrid[simKey][refIDIndex] = numWetHarvest[simKey]
								if maxWetHarvest < numWetHarvest[simKey] {
									maxWetHarvest = numWetHarvest[simKey]
								}
							} else {
								wetHarvestGrid[simKey][refIDIndex] = -1
							}
						} else {
							coolWeatherImpactGrid[simKey][refIDIndex] = -100
							coolWeatherDeathGrid[simKey][refIDIndex] = -10000
							coolWeatherImpactWeightGrid[simKey][refIDIndex] = -1
							wetHarvestGrid[simKey][refIDIndex] = -1
						}
					}
				}
			}
		}
		currentInput++
		if showBar {
			progessFunc(currentInput)
		}
	}

	drawDateMaps(gridSourceLookup,
		matIsHavestGrid,
		asciiOutFilenameMatIsHarvest,
		extCol, extRow,
		asciiOutFolder,
		"Harvest before maturity - Scn: %v %v %v",
		"counted occurrences in 30 years",
		showBar,
		"inferno",
		nil, nil, 1.0, 0,
		maxMatHarvest, "Harvest before maturity")

	drawDateMaps(gridSourceLookup,
		lateHarvestGrid,
		asciiOutFilenameLateHarvest,
		extCol, extRow,
		asciiOutFolder,
		"Auto Harvest 31. October - Scn: %v %v %v",
		"counted occurrences in 30 years",
		showBar,
		"viridis",
		nil, nil, 1.0, 0,
		maxLateHarvest,
		"Harvest 31. October")

	drawDateMaps(gridSourceLookup,
		wetHarvestGrid,
		asciiOutFilenameWetHarvest,
		extCol, extRow,
		asciiOutFolder,
		"Rain during/before harvest - Scn: %v %v %v",
		"counted occurrences in 30 years",
		showBar,
		"nipy_spectral",
		nil, nil, 1.0, 0,
		maxWetHarvest,
		"wet harvest")

	drawDateMaps(gridSourceLookup,
		coolWeatherImpactGrid,
		asciiOutFilenameCoolWeather,
		extCol, extRow,
		asciiOutFolder,
		"Cool weather occurrence - Scn: %v %v %v",
		"counted occurrences in 30 years",
		showBar,
		"nipy_spectral",
		nil, nil, 1.0, 0,
		sumMaxOccurrence,
		"Cool weather")

	coolWeatherWeightLabels := []string{"0", "< 15°C", "< 10°C", "< 8°C"}
	ticklist := []float64{0, 3, 7, 11}
	drawDateMaps(gridSourceLookup,
		coolWeatherImpactWeightGrid,
		asciiOutFilenameCoolWeatherWeight,
		extCol, extRow,
		asciiOutFolder,
		"Cool weather weight - Scn: %v %v %v",
		"weights for occurrences in 30 years",
		showBar,
		"gnuplot",
		coolWeatherWeightLabels, ticklist, 1.0, 0, 12,
		"Cool weather")
	drawDateMaps(gridSourceLookup,
		coolWeatherDeathGrid,
		asciiOutFilenameCoolWeather,
		extCol, extRow,
		asciiOutFolder,
		"Cool weather severity - Scn: %v %v %v",
		"counted occurrences with severity factor",
		showBar,
		"nipy_spectral",
		nil, nil, 0.0001, 0,
		sumMaxDeathOccurrence,
		"Cool weather death")

	drawDateMaps(gridSourceLookup,
		allGrids,
		asciiOutFilenameAvg,
		extCol, extRow,
		asciiOutFolder,
		"Average Yield - Scn: %v %v %v",
		"Yield in t",
		showBar,
		"viridis",
		nil, nil, 1.0, 0.0,
		int(maxAllAvgYield),
		"average yield grids")

	drawDateMaps(gridSourceLookup,
		StdDevAvgGrids,
		asciiOutFilenameDeviAvg,
		extCol, extRow,
		asciiOutFolder,
		"Std Deviation - Scn: %v %v %v",
		"standart deviation",
		showBar,
		"cool",
		nil, nil, 1.0, 0,
		int(maxSdtDeviation),
		"std average yield grids")

	// Start calculate max yield layer and maturity layer grid
	numKeys := len(allGrids)
	maxYieldGrids := make(map[ScenarioKeyTuple][]int, numKeys)
	matGroupGrids := make(map[ScenarioKeyTuple][]int, numKeys)
	maxYieldDeviationGrids := make(map[ScenarioKeyTuple][]int, numKeys)
	matGroupDeviationGrids := make(map[ScenarioKeyTuple][]int, numKeys)
	matGroupIDGrids := make(map[string]int)
	matIdcounter := 0
	matGroupIDGrids["none"] = matIdcounter //# maturity group id for 'no yield'
	// set ids for each maturity group
	for simKey := range allGrids {
		if _, ok := matGroupIDGrids[simKey.mGroup]; !ok {
			matIdcounter++
			matGroupIDGrids[simKey.mGroup] = matIdcounter
		}

	}
	for simKey, currGrid := range allGrids {
		//treatmentNoIdx, climateSenarioIdx, mGroupIdx, commentIdx
		scenarioKey := ScenarioKeyTuple{simKey.treatNo, simKey.climateSenario, simKey.comment}
		if _, ok := maxYieldGrids[scenarioKey]; !ok {
			maxYieldGrids[scenarioKey] = newGridLookup(maxRefNo, NONEVALUE)
			matGroupGrids[scenarioKey] = newGridLookup(maxRefNo, NONEVALUE)
			maxYieldDeviationGrids[scenarioKey] = newGridLookup(maxRefNo, NONEVALUE)
			matGroupDeviationGrids[scenarioKey] = newGridLookup(maxRefNo, NONEVALUE)
		}

		for ref := 0; ref < maxRefNo; ref++ {
			if currGrid[ref] > maxYieldGrids[scenarioKey][ref] {
				maxYieldGrids[scenarioKey][ref] = currGrid[ref]
				maxYieldDeviationGrids[scenarioKey][ref] = currGrid[ref]
				if currGrid[ref] == 0 {
					matGroupGrids[scenarioKey][ref] = matGroupIDGrids["none"]
					matGroupDeviationGrids[scenarioKey][ref] = matGroupIDGrids["none"]
				} else {
					matGroupGrids[scenarioKey][ref] = matGroupIDGrids[simKey.mGroup]
					matGroupDeviationGrids[scenarioKey][ref] = matGroupIDGrids[simKey.mGroup]
				}
			}
		}
	}
	invMatGroupIDGrids := make(map[int]string, len(matGroupIDGrids))
	for k, v := range matGroupIDGrids {
		invMatGroupIDGrids[v] = k
	}

	for simKey, currGridYield := range allGrids {
		//#treatmentNoIdx, climateSenarioIdx, mGroupIdx, CommentIdx
		scenarioKey := ScenarioKeyTuple{simKey.treatNo, simKey.climateSenario, simKey.comment}
		currGridDeviation := StdDevAvgGrids[simKey]
		for ref := 0; ref < maxRefNo; ref++ {
			if matGroupDeviationGrids[scenarioKey][ref] != NONEVALUE {
				matGroup := invMatGroupIDGrids[matGroupDeviationGrids[scenarioKey][ref]]
				matGroupKey := SimKeyTuple{simKey.treatNo, simKey.climateSenario, matGroup, simKey.comment}
				if float64(currGridYield[ref]) > float64(maxYieldGrids[scenarioKey][ref])*0.9 &&
					currGridDeviation[ref] < StdDevAvgGrids[matGroupKey][ref] {
					maxYieldDeviationGrids[scenarioKey][ref] = currGridYield[ref]
					matGroupDeviationGrids[scenarioKey][ref] = matGroupIDGrids[simKey.mGroup]
				}
			}
		}
	}

	var progressBar func(int)
	if showBar {
		numInput = len(maxYieldDeviationGrids)
		progressBar = progress(numInput, "max yields dev grids")
	}
	for scenarioKey, scenarioVal := range maxYieldDeviationGrids {
		//# ASCII_OUT_FILENAME_MAX_YIELD = "maxyield_trno{1}.asc" # treatmentnumber
		gridFileName := fmt.Sprintf(asciiOutFilenameMaxYieldDevi, scenarioKey.treatNo)
		gridFileName = strings.ReplaceAll(gridFileName, "/", "-") //remove directory seperator from filename
		gridFilePath := filepath.Join(asciiOutFolder, scenarioKey.climateSenario, gridFileName)
		//# create ascii file
		file := writeAGridHeader(gridFilePath, extCol, extRow)
		writeRows(file, extRow, extCol, scenarioVal, gridSourceLookup)
		file.Close()

		title := fmt.Sprintf("Max avg yield minus std deviation - Scn: %s %s", scenarioKey.climateSenario, scenarioKey.comment)
		labelText := "Yield in t"
		colormap := "jet"
		writeMetaFile(gridFilePath, title, labelText, colormap, nil, nil, nil, 0.001, int(maxAllAvgYield), 0)
		currentInput++
		if showBar {
			progressBar(currentInput)
		}
	}
	if showBar {
		numInput = len(maxYieldGrids)
		progressBar = progress(numInput, "max yields grids")
	}
	for scenarioKey, scenarioVal := range maxYieldGrids {
		gridFileName := fmt.Sprintf(asciiOutFilenameMaxYield, scenarioKey.treatNo)
		gridFileName = strings.ReplaceAll(gridFileName, "/", "-") //remove directory seperator from filename
		gridFilePath := filepath.Join(asciiOutFolder, scenarioKey.climateSenario, gridFileName)

		// create ascii file
		file := writeAGridHeader(gridFilePath, extCol, extRow)
		writeRows(file, extRow, extCol, scenarioVal, gridSourceLookup)
		file.Close()
		title := fmt.Sprintf("Max average yield - Scn: %s %s", scenarioKey.climateSenario, scenarioKey.comment)
		labelText := "Yield in t"
		colormap := "jet"
		writeMetaFile(gridFilePath, title, labelText, colormap, nil, nil, nil, 0.001, int(maxAllAvgYield), 0)
		currentInput++
		if showBar {
			progressBar(currentInput)
		}
	}
	if showBar {
		numInput = len(matGroupGrids)
		progressBar = progress(numInput, "mat groups grids")
	}
	sidebarLabel := make([]string, len(matGroupIDGrids)+1)
	colorList := []string{"cyan", "lightgreen", "magenta", "crimson", "blue", "gold", "navy"}

	for id := range matGroupIDGrids {
		sidebarLabel[matGroupIDGrids[id]] = id
	}
	ticklist = make([]float64, len(sidebarLabel))
	for tick := 0; tick < len(ticklist); tick++ {
		ticklist[tick] = float64(tick) + 0.5
	}

	for scenarioKey, scenarioVal := range matGroupGrids {
		gridFileName := fmt.Sprintf(asciiOutFilenameMaxYieldMat, scenarioKey.treatNo)
		gridFileName = strings.ReplaceAll(gridFileName, "/", "-") //remove directory seperator from filename
		gridFilePath := filepath.Join(asciiOutFolder, scenarioKey.climateSenario, gridFileName)

		// create ascii file
		file := writeAGridHeader(gridFilePath, extCol, extRow)
		writeRows(file, extRow, extCol, scenarioVal, gridSourceLookup)
		file.Close()
		// create png
		title := fmt.Sprintf("Maturity groups for max average yield - Scn: %s %s", scenarioKey.climateSenario, scenarioKey.comment)
		writeMetaFile(gridFilePath, title, "Maturity Group", "", colorList, sidebarLabel, ticklist, 1.0, len(sidebarLabel)-1, 0)
		currentInput++
		if showBar {
			progressBar(currentInput)
		}
	}

	currentInput = 0
	numInput = len(matGroupDeviationGrids)
	if showBar {
		numInput = len(matGroupDeviationGrids)
		progressBar = progress(numInput, "mat groups grids devi")
	}
	for scenarioKey, scenarioVal := range matGroupGrids {
		gridFileName := fmt.Sprintf(asciiOutFilenameMaxYieldMatDevi, scenarioKey.treatNo)
		gridFileName = strings.ReplaceAll(gridFileName, "/", "-") //remove directory seperator from filename
		gridFilePath := filepath.Join(asciiOutFolder, scenarioKey.climateSenario, gridFileName)

		file := writeAGridHeader(gridFilePath, extCol, extRow)
		writeRows(file, extRow, extCol, scenarioVal, gridSourceLookup)
		file.Close()

		title := fmt.Sprintf("Maturity groups - max avg yield minus deviation  - Scn: %s %s", scenarioKey.climateSenario, scenarioKey.comment)
		writeMetaFile(gridFilePath, title, "Maturity Group", "", colorList, sidebarLabel, ticklist, 1.0, len(sidebarLabel)-1, 0)
		currentInput++
		if showBar {
			progressBar(currentInput)
		}
	}

	// Grid Diff affected by water stress T4(potential) - T1(actual)
	currentInput = 0
	if showBar {
		numInput = len(allGrids)
		progressBar = progress(numInput, "water diff grids")
	}
	for simKey, simValue := range allGrids {
		//# treatment number
		if simKey.treatNo == "T1" {
			otherKey := SimKeyTuple{"T2", simKey.climateSenario, simKey.mGroup, "Unlimited water"}
			newDiffGrid := gridDifference(allGrids[otherKey], simValue, maxRefNo)

			gridFileName := fmt.Sprintf(asciiOutFilenameWaterDiff, simKey.treatNo)
			gridFileName = strings.ReplaceAll(gridFileName, "/", "-") //remove directory seperator from filename
			gridFilePath := filepath.Join(asciiOutFolder, simKey.climateSenario, gridFileName)

			file := writeAGridHeader(gridFilePath, extCol, extRow)
			writeRows(file, extRow, extCol, newDiffGrid, gridSourceLookup)
			file.Close()
			title := fmt.Sprintf("Water stress effect on potential yield - Scn: %s %s", simKey.climateSenario, simKey.comment)
			labelText := "Difference yield in t"
			colormap := "Wistia"
			writeMetaFile(gridFilePath, title, labelText, colormap, nil, nil, nil, 0.001, int(maxAllAvgYield), 0)
			currentInput++
			if showBar {
				progressBar(currentInput)
			}
		}
	}
	currentInput = 0
	if showBar {
		numInput = len(maxYieldGrids)
		progressBar = progress(numInput, "water diff grids max")
	}
	for scenarioKey, simValue := range maxYieldGrids {
		// treatment number
		if scenarioKey.treatNo == "T1" {
			otherKey := ScenarioKeyTuple{"T2", scenarioKey.climateSenario, "Unlimited water"}
			newDiffGrid := gridDifference(maxYieldGrids[otherKey], simValue, maxRefNo)

			gridFilePath := filepath.Join(asciiOutFolder, scenarioKey.climateSenario, asciiOutFilenameWaterDiffMax)

			file := writeAGridHeader(gridFilePath, extCol, extRow)
			writeRows(file, extRow, extCol, newDiffGrid, gridSourceLookup)
			file.Close()
			title := fmt.Sprintf("Water stress effect on potential max yield - Scn: %s", scenarioKey.climateSenario)
			labelText := "Difference yield in t"
			colormap := "Wistia"
			writeMetaFile(gridFilePath, title, labelText, colormap, nil, nil, nil, 0.001, int(maxAllAvgYield), 0)
		}
		currentInput++
		if showBar {
			progressBar(currentInput)
		}
	}
	fmt.Println(" ")
	fmt.Printf("Low: %v", sumLowOccurrence)
	fmt.Printf("Medium: %v", sumMediumOccurrence)
	fmt.Printf("High: %v", sumHighOccurrence)
}

// SimKeyTuple key to identify each simulatio setup
type SimKeyTuple struct {
	treatNo        string
	climateSenario string
	mGroup         string
	comment        string
}

//ScenarioKeyTuple ...
type ScenarioKeyTuple struct {
	treatNo        string
	climateSenario string
	comment        string
}

// SimData simulation data from a line
type SimData struct {
	period   string
	year     int
	sowDOY   int
	emergDOY int
	antDOY   int
	matDOY   int
	harDOY   int
	yields   float64
}

// GridCoord tuple of positions
type GridCoord struct {
	row int
	col int
}

// SimDataIndex indices for climate data
type SimDataIndex struct {
	treatNoIdx        int
	climateSenarioIdx int
	mGroupIdx         int
	commentIdx        int
	periodIdx         int
	yearIdx           int
	sowDOYIdx         int
	emergDOYIdx       int
	antDOYIdx         int
	matDOYIdx         int
	harvDOYIdx        int
	yieldsIdx         int
}

func readHeader(line string) SimDataIndex {
	//read header
	tokens := strings.Split(line, ",")
	indices := SimDataIndex{
		treatNoIdx:        -1,
		climateSenarioIdx: -1,
		mGroupIdx:         -1,
		commentIdx:        -1,
		periodIdx:         -1,
		yearIdx:           -1,
		sowDOYIdx:         -1,
		emergDOYIdx:       -1,
		antDOYIdx:         -1,
		matDOYIdx:         -1,
		harvDOYIdx:        -1,
		yieldsIdx:         -1,
	}

	for i, token := range tokens {
		switch token {
		case "Crop":
			indices.mGroupIdx = i
		case "sce":
			indices.climateSenarioIdx = i
		case "Yield":
			indices.yieldsIdx = i
		case "ProductionCase":
			indices.commentIdx = i
		case "TrtNo":
			indices.treatNoIdx = i
		case "EmergDOY":
			indices.emergDOYIdx = i
		case "SowDOY":
			indices.sowDOYIdx = i
		case "AntDOY":
			indices.antDOYIdx = i
		case "MatDOY":
			indices.matDOYIdx = i
		case "HarvDOY":
			indices.harvDOYIdx = i
		case "Year":
			indices.yearIdx = i
		case "period":
			indices.periodIdx = i
		}
	}
	return indices
}

func loadLine(line string, header SimDataIndex) (SimKeyTuple, SimData) {
	// read relevant content from line
	tokens := strings.Split(line, ",")
	var key SimKeyTuple
	var content SimData
	key.treatNo = tokens[header.treatNoIdx]
	key.climateSenario = tokens[header.climateSenarioIdx]
	key.mGroup = tokens[header.mGroupIdx]
	key.comment = tokens[header.commentIdx]
	content.period = tokens[header.periodIdx]
	val, err := strconv.ParseInt(tokens[header.yearIdx], 10, 0)
	if err != nil {
		log.Fatal(err)
	}
	content.year = int(val)
	content.sowDOY = validDOY(tokens[header.sowDOYIdx])
	content.emergDOY = validDOY(tokens[header.emergDOYIdx])
	content.antDOY = validDOY(tokens[header.antDOYIdx])
	content.matDOY = validDOY(tokens[header.matDOYIdx])
	content.harDOY = validDOY(tokens[header.harvDOYIdx])
	content.yields, _ = strconv.ParseFloat(tokens[header.yieldsIdx], 64)
	return key, content
}

func validDOY(s string) int {
	// return a valid DOY or -1 from string
	value, err := strconv.ParseInt(s, 10, 0)
	if err != nil {
		return -1
	}
	return int(value)
}

//ClimateHeader ...
type ClimateHeader struct {
	isodateIdx int
	tminIdx    int
	precipIdx  int
}

//ClimateContent ..
type ClimateContent struct {
	isodate time.Time
	tmin    float64
	precip  float64
}

//ReadClimateHeader ..
func ReadClimateHeader(line string) ClimateHeader {
	header := ClimateHeader{-1, -1, -1}
	//read header
	tokens := strings.Split(line, ",")
	for i, token := range tokens {
		if token == "iso-date" {
			header.isodateIdx = i
		}
		if token == "tmin" {
			header.tminIdx = i
		}
		if token == "precip" {
			header.precipIdx = i
		}
	}
	return header
}

func loadClimateLine(line string, header ClimateHeader) ClimateContent {
	var cC ClimateContent
	tokens := strings.Split(line, ",")
	cC.isodate, _ = time.Parse("2006-01-02", tokens[header.isodateIdx])
	cC.tmin, _ = strconv.ParseFloat(tokens[header.tminIdx], 64)
	cC.precip, _ = strconv.ParseFloat(tokens[header.precipIdx], 64)
	return cC
}

func newGridLookup(maxRef, defaultVal int) []int {
	grid := make([]int, maxRef)
	for i := 0; i < maxRef; i++ {
		grid[i] = defaultVal
	}
	return grid
}

// GetGridLookup ..
func GetGridLookup(gridsource string) (rowExt int, colExt int, lookupGrid [][]int) {
	colExt = 0
	rowExt = 0
	lookup := make(map[int64][]GridCoord)

	sourcefile, err := os.Open(gridsource)
	if err != nil {
		log.Fatal(err)
	}
	defer sourcefile.Close()
	firstLine := true
	colID := -1
	rowID := -1
	refID := -1
	scanner := bufio.NewScanner(sourcefile)
	for scanner.Scan() {
		line := scanner.Text()
		tokens := strings.Split(line, ",")
		if firstLine {
			firstLine = false
			for index, token := range tokens {
				if token == "Column_" {
					colID = index
				}
				if token == "Row" {
					rowID = index
				}
				if token == "soil_ref" {
					refID = index
				}
			}
		} else {
			col, _ := strconv.ParseInt(tokens[colID], 10, 64)
			row, _ := strconv.ParseInt(tokens[rowID], 10, 64)
			ref, _ := strconv.ParseInt(tokens[refID], 10, 64)
			if int(col) > colExt {
				colExt = int(col)
			}
			if int(row) > rowExt {
				rowExt = int(row)
			}
			if _, ok := lookup[ref]; !ok {
				lookup[ref] = make([]GridCoord, 0, 1)
			}
			lookup[ref] = append(lookup[ref], GridCoord{int(row), int(col)})
		}
	}
	lookupGrid = newGrid(rowExt, colExt, NONEVALUE)
	for ref, coord := range lookup {
		for _, rowCol := range coord {
			lookupGrid[rowCol.row-1][rowCol.col-1] = int(ref)
		}
	}

	return rowExt, colExt, lookupGrid
}

// GetClimateReference ..
func GetClimateReference(refSource string) map[int]string {
	lookup := make(map[int]string)
	sourcefile, err := os.Open(refSource)
	if err != nil {
		log.Fatal(err)
	}
	defer sourcefile.Close()
	scanner := bufio.NewScanner(sourcefile)
	firstLine := true
	refID := -1
	climateID := -1
	for scanner.Scan() {
		line := scanner.Text()
		tokens := strings.Split(line, ",")
		if firstLine {
			// read header
			firstLine = false
			for index, token := range tokens {
				if token == "CLocation" {
					climateID = index
				}
				if token == "soil_ref" {
					refID = index
				}
			}
		} else {
			climate := tokens[climateID]
			ref, _ := strconv.ParseInt(tokens[refID], 10, 64)
			lookup[int(ref)] = climate
		}
	}
	return lookup
}

func newGrid(extRow, extCol, defaultVal int) [][]int {
	grid := make([][]int, extRow)
	for r := 0; r < extRow; r++ {
		grid[r] = make([]int, extCol)
		for c := 0; c < extCol; c++ {
			grid[r][c] = defaultVal
		}
	}
	return grid
}

// IsCrop ...
func IsCrop(key SimKeyTuple, cropName string) bool {
	return strings.HasPrefix(key.mGroup, cropName)
}
func average(list []float64) float64 {
	sum := 0.0
	val := 0.0
	lenVal := 0.0
	for _, x := range list {
		if x >= 0 {
			sum = sum + x
			lenVal++
		}
	}
	if lenVal > 0 {
		val = sum / lenVal
	}

	return val
}

func averageInt(list []int) int {
	sum := 0
	val := 0
	lenVal := 0
	for _, x := range list {
		if x >= 0 {
			sum = sum + x
			lenVal++
		}
	}
	if lenVal > 0 {
		val = sum / lenVal
	}

	return val
}

// CalculatePixel yield average for stable yield set
func CalculatePixel(yieldList []float64) float64 {
	pixelValue := average(yieldList)
	if HasUnStableYield(yieldList, pixelValue) {
		pixelValue = 0
	}
	return pixelValue
}

//HasUnStableYield adjust this methode to define if yield loss is too hight
func HasUnStableYield(yieldList []float64, averageValue float64) bool {
	unstable := false
	counter := 0
	lowPercent := averageValue * 0.2
	for _, y := range yieldList {
		if y < 900 || y < lowPercent {
			counter++
		}
	}
	if counter > 3 {
		unstable = true
	}
	return unstable
}

// IsDateInGrowSeason ...
func IsDateInGrowSeason(startDOY, endDOY int, date time.Time) bool {
	doy := date.YearDay()
	if doy >= startDOY && doy <= endDOY {
		return true
	}
	return false
}

func makeDir(outPath string) {
	dir := filepath.Dir(outPath)
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		if err := os.MkdirAll(dir, os.ModePerm); err != nil {
			log.Fatalf("ERROR: Failed to generate output path %s :%v", dir, err)
		}
	}
}

func gridDifference(grid1, grid2 []int, maxRef int) []int {
	// calculate the difference between 2 grids, save it to new grid
	newGridDiff := newGridLookup(maxRef, NONEVALUE)
	for ref := 0; ref < maxRef; ref++ {
		if grid1[ref] != NONEVALUE && grid2[ref] != NONEVALUE {
			newGridDiff[ref] = grid1[ref] - grid2[ref]
		} else {
			newGridDiff[ref] = NONEVALUE
		}
	}
	return newGridDiff
}

func progress(total int, status string) func(int) {
	count := total
	current := 0
	bar := pb.New(count)
	// show percents (by default already true)
	bar.ShowPercent = true
	//show bar (by default already true)
	bar.ShowBar = true
	bar.ShowCounters = true
	bar.ShowTimeLeft = true
	bar.Start()
	return func(newCurrent int) {
		if newCurrent > current {
			inc := newCurrent - current

			for i := 0; i < inc && current < count; i++ {
				current++
				if current == count {
					bar.FinishPrint("The End!")
				}
				bar.Increment()
			}
		}
	}
}

type dataLastDays struct {
	arr        []float64
	index      int
	currentLen int
	capacity   int
}

func newDataLastDays(days int) dataLastDays {
	return dataLastDays{arr: make([]float64, days), index: 0, capacity: days}
}

func (d *dataLastDays) addDay(val float64) {
	if d.index < d.capacity-1 {
		d.index++
		if d.currentLen < d.capacity {
			d.currentLen++
		}
	} else {
		d.index = 0
	}
	d.arr[d.index] = val
}

func (d *dataLastDays) getData() []float64 {
	if d.currentLen == 0 {
		return nil
	}
	return d.arr[:d.currentLen]
}

func drawDateMaps(gridSourceLookup [][]int, grids map[SimKeyTuple][]int, filenameFormat string, extCol, extRow int, asciiOutFolder, titleFormat, labelText string, showBar bool, colormap string, cbarLabel []string, ticklist []float64, factor float64, minVal, maxVal int, progessStatus string) {

	var currentInput int
	var numInput int
	var progressBar func(int)
	if showBar {
		numInput = len(grids)
		progressBar = progress(numInput, progessStatus)
	}

	for simKey, simVal := range grids {
		//simkey = treatmentNo, climateSenario, maturityGroup, comment
		gridFileName := fmt.Sprintf(filenameFormat, simKey.mGroup, simKey.treatNo)
		gridFileName = strings.ReplaceAll(gridFileName, "/", "-") //remove directory seperator from filename
		gridFilePath := filepath.Join(asciiOutFolder, simKey.climateSenario, gridFileName)
		file := writeAGridHeader(gridFilePath, extCol, extRow)

		writeRows(file, extRow, extCol, simVal, gridSourceLookup)
		file.Close()
		title := fmt.Sprintf(titleFormat, simKey.climateSenario, simKey.mGroup, simKey.comment)
		writeMetaFile(gridFilePath, title, labelText, colormap, nil, cbarLabel, ticklist, factor, maxVal, minVal)

		if showBar {
			currentInput++
			progressBar(currentInput)
		}
	}
}
func writeAGridHeader(name string, nCol, nRow int) (fout Fout) {
	cornerX := 0.0
	cornery := 0.0
	novalue := -9999
	cellsize := 1.0
	// create an ascii file, which contains the header
	makeDir(name)
	file, err := os.OpenFile(name+".gz", os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0600)
	if err != nil {
		log.Fatal(err)
	}

	gfile := gzip.NewWriter(file)
	fwriter := bufio.NewWriter(gfile)
	fout = Fout{file, gfile, fwriter}

	fout.Write(fmt.Sprintf("ncols %d\n", nCol))
	fout.Write(fmt.Sprintf("nrows %d\n", nRow))
	fout.Write(fmt.Sprintf("xllcorner     %f\n", cornerX))
	fout.Write(fmt.Sprintf("yllcorner     %f\n", cornery))
	fout.Write(fmt.Sprintf("cellsize      %f\n", cellsize))
	fout.Write(fmt.Sprintf("NODATA_value  %d\n", novalue))

	return fout
}

func writeRows(fout Fout, extRow, extCol int, simGrid []int, gridSourceLookup [][]int) {
	//TODO: this func is bullshit
	//line := ""

	for row := 0; row < extRow; row++ {

		for col := 0; col < extCol; col++ {
			refID := gridSourceLookup[row][col]
			if refID >= 0 {
				fout.Write(strconv.Itoa(simGrid[refID-1]))
				fout.Write(" ")
				//line += fmt.Sprintf("%d ", simGrid[refID-1])
			} else {
				fout.Write("-9999 ")
				//line += "-9999 "
			}
		}
		fout.Write("\n")
		//line += "\n"
	}
	//file.WriteString(line)
}

// Fout combined file writer
type Fout struct {
	file    *os.File
	gfile   *gzip.Writer
	fwriter *bufio.Writer
}

// Write string to zip file
func (f Fout) Write(s string) {
	f.fwriter.WriteString(s)
}

// Close file writer
func (f Fout) Close() {
	f.fwriter.Flush()
	// Close the gzip first.
	f.gfile.Close()
	f.file.Close()
}

func writeMetaFile(gridFilePath, title, labeltext, colormap string, colorlist []string, cbarLabel []string, ticklist []float64, factor float64, maxValue, minValue int) {
	metaFilePath := gridFilePath + ".meta"
	makeDir(metaFilePath)
	file, err := os.OpenFile(metaFilePath, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0600)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()
	file.WriteString(fmt.Sprintf("title: '%s'\n", title))
	file.WriteString(fmt.Sprintf("labeltext: '%s'\n", labeltext))
	if colormap != "" {
		file.WriteString(fmt.Sprintf("colormap: '%s'\n", colormap))
	}
	if colorlist != nil {
		file.WriteString("colorlist: \n")
		for _, item := range colorlist {
			file.WriteString(fmt.Sprintf(" - '%s'\n", item))
		}
	}
	if cbarLabel != nil {
		file.WriteString("cbarLabel: \n")
		for _, cbarItem := range cbarLabel {
			file.WriteString(fmt.Sprintf(" - '%s'\n", cbarItem))
		}
	}
	if ticklist != nil {
		file.WriteString("ticklist: \n")
		for _, tick := range ticklist {
			file.WriteString(fmt.Sprintf(" - %f\n", tick))
		}
	}
	file.WriteString(fmt.Sprintf("factor: %f\n", factor))
	if maxValue != NONEVALUE {
		file.WriteString(fmt.Sprintf("maxValue: %d\n", maxValue))
	}
	if minValue != NONEVALUE {
		file.WriteString(fmt.Sprintf("minValue: %d\n", minValue))
	}
}

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
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	"gonum.org/v1/gonum/stat"
)

// USER switch for setting
const USER = "local"

// CROPNAME to analyse
const CROPNAME = "soybean"

// NONEVALUE for ascii table
const NONEVALUE = -9999

const climateFilePattern = "%s_v3test.csv"

// output pattern
const asciiOutTemplate = "%s_%s_trno%s.asc"  // <descriptio>_<scenario>_<treatmentnumber>
const asciiOutCombinedTemplate = "%s_%s.asc" // <descriptio>_<scenario>

func main() {

	PATHS := map[string]map[string]string{
		"local": {
			"projectdatapath": "./",
			"outputpath":      ".",
			"climate-data":    "./climate-data/corrected/",  // path to climate data
			"ascii-out":       "asciigrids_combined_debug/", // path to ascii grids
		},
		"Cluster": {
			"projectdatapath": "/project/",
			"outputpath":      "/out/",
			"climate-data":    "/climate-data/",      // path to climate data
			"ascii-out":       "asciigrid_combined/", // path to ascii grids
		},
	}
	pathPtr := flag.String("path", USER, "path id")
	source1Ptr := flag.String("source1", "", "path to source folder")
	source2Ptr := flag.String("source2", "", "path to source folder")
	source3Ptr := flag.String("source3", "", "path to source folder")
	source4Ptr := flag.String("source4", "", "path to source folder")
	outPtr := flag.String("out", "", "path to out folder")
	projectPtr := flag.String("project", "", "path to project folder")
	climatePtr := flag.String("climate", "", "path to climate folder")

	flag.Parse()

	pathID := *pathPtr
	outputFolder := *outPtr
	climateFolder := *climatePtr
	projectpath := *projectPtr

	sourceFolder := make([]string, 0, 4)
	if len(*source1Ptr) > 0 {
		sourceFolder = append(sourceFolder, *source1Ptr)
	}
	if len(*source2Ptr) > 0 {
		sourceFolder = append(sourceFolder, *source2Ptr)
	}
	if len(*source3Ptr) > 0 {
		sourceFolder = append(sourceFolder, *source3Ptr)
	}
	if len(*source4Ptr) > 0 {
		sourceFolder = append(sourceFolder, *source4Ptr)
	}
	if len(outputFolder) == 0 {
		outputFolder = PATHS[pathID]["outputpath"]
	}
	if len(climateFolder) == 0 {
		climateFolder = PATHS[pathID]["climate-data"]
	}
	if len(projectpath) == 0 {
		projectpath = PATHS[pathID]["projectdatapath"]
	}

	asciiOutFolder := filepath.Join(outputFolder, PATHS[pathID]["ascii-out"])
	gridSource := filepath.Join(projectpath, "stu_eu_layer_grid.csv")
	refSource := filepath.Join(projectpath, "stu_eu_layer_ref.csv")

	extRow, extCol, gridSourceLookup := GetGridLookup(gridSource)
	climateRef := GetClimateReference(refSource)

	numSourceFolder := len(sourceFolder)
	outMaxRefNoC := make(chan int)
	filelists := make(map[int][]os.FileInfo, numSourceFolder)
	for i := 0; i < numSourceFolder; i++ {
		go func(idxSource int, sourceFolder string, out chan int) {
			filelist, err := ioutil.ReadDir(sourceFolder)
			if err != nil {
				log.Fatal(err)
			}
			filelists[idxSource] = filelist
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

			out <- maxRefNo
		}(i, sourceFolder[i], outMaxRefNoC)
	}
	receivedResults := 0
	maxRefNoOverAll := 0
	for receivedResults < numSourceFolder {
		select {
		case maxRefNo := <-outMaxRefNoC:
			if maxRefNoOverAll < maxRefNo {
				maxRefNoOverAll = maxRefNo
			}
			receivedResults++
		}
	}
	fmt.Println("Number of References:", maxRefNoOverAll)

	var p ProcessedData
	p.initProcessedData()

	// part 1: get all data
	currRuns := 0
	maxRuns := 60
	outChan := make(chan bool)
	for idxSource, filelist := range filelists {
		for _, sourcefileInfo := range filelist {
			go func(idxSource int, sourcefileName string, outC chan bool) {
				sourcefile, err := os.Open(filepath.Join(sourceFolder[idxSource], sourcefileName))
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
				simDoySow := make(map[SimKeyTuple][]int)
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
							sowValue := lineContent.sowDOY
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
								simDoySow[lineKey] = make([]int, 0, 30)
								dateYearOrder[lineKey] = make([]int, 0, 30)
							}
							p.setClimateFilePeriod(lineKey.climateSenario, period)

							simulations[lineKey] = append(simulations[lineKey], yieldValue)
							simDoySow[lineKey] = append(simDoySow[lineKey], sowValue)
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
				p.setOutputGridsGenerated(simulations, numSourceFolder, maxRefNoOverAll)
				for simKey := range simulations {
					pixelValue := CalculatePixel(simulations[simKey])
					p.setMaxAllAvgYield(pixelValue)
					stdDeviation := stat.StdDev(simulations[simKey], nil)
					p.setMaxSdtDeviation(stdDeviation)

					p.harvestGrid[simKey][idxSource][refIDIndex] = averageInt(simDoyHarvest[simKey])
					sum := 0
					for _, val := range simMatIsHarvest[simKey] {
						if val {
							sum++
						}
					}
					p.matIsHavestGrid[simKey][idxSource][refIDIndex] = sum
					sum = 0
					for _, val := range simLastHarvestDate[simKey] {
						if val {
							sum++
						}
					}
					p.lateHarvestGrid[simKey][idxSource][refIDIndex] = sum
					p.allYieldGrids[simKey][idxSource][refIDIndex] = int(pixelValue)
					p.StdDevAvgGrids[simKey][idxSource][refIDIndex] = int(stdDeviation)

					p.setMaxLateHarvest(p.lateHarvestGrid[simKey][idxSource][refIDIndex])
					p.setMaxMatHarvest(p.matIsHavestGrid[simKey][idxSource][refIDIndex])
				}
				//coolWeatherImpactGrid
				for scenario := range p.climateFilePeriod {
					climateRowCol := climateRef[refIDIndex]
					climatePath := filepath.Join(climateFolder, p.climateFilePeriod[scenario], scenario, fmt.Sprintf(climateFilePattern, climateRowCol))
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
								if p.allYieldGrids[simKey][idxSource][refIDIndex] > 0 {
									if _, ok := numOccurrenceMedium[simKey]; ok {
										sumOccurrence := numOccurrenceMedium[simKey] + numOccurrenceHigh[simKey] + numOccurrenceLow[simKey]
										sumDeathOccurrence := numOccurrenceMedium[simKey]*10 + numOccurrenceHigh[simKey]*100 + numOccurrenceLow[simKey]

										p.setSumLowOccurrence(numOccurrenceLow[simKey])
										p.setSumMediumOccurrence(numOccurrenceMedium[simKey])
										p.setSumHighOccurrence(numOccurrenceHigh[simKey])

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
										p.coolWeatherImpactGrid[simKey][idxSource][refIDIndex] = sumOccurrence
										p.coolWeatherDeathGrid[simKey][idxSource][refIDIndex] = sumDeathOccurrence
										p.coolWeatherImpactWeightGrid[simKey][idxSource][refIDIndex] = weight
										p.setSumMaxOccurrence(sumOccurrence)
										p.setSumMaxDeathOccurrence(sumDeathOccurrence)
									} else {
										p.coolWeatherImpactGrid[simKey][idxSource][refIDIndex] = 0
										p.coolWeatherDeathGrid[simKey][idxSource][refIDIndex] = 0
									}
									// wet harvest occurence
									if _, ok := numWetHarvest[simKey]; ok {
										p.wetHarvestGrid[simKey][idxSource][refIDIndex] = numWetHarvest[simKey]
										p.setMaxWetHarvest(numWetHarvest[simKey])
									}
									// else {
									// 	p.wetHarvestGrid[simKey][idxSource][refIDIndex] = -1
									// }
								}
								// else {
								// 	p.coolWeatherImpactGrid[simKey][idxSource][refIDIndex] = -100
								// 	p.coolWeatherDeathGrid[simKey][idxSource][refIDIndex] = -1
								// 	p.coolWeatherImpactWeightGrid[simKey][idxSource][refIDIndex] = -1
								// 	p.wetHarvestGrid[simKey][idxSource][refIDIndex] = -1
								// }
							}
						}
					}
				}
				outChan <- true
			}(idxSource, sourcefileInfo.Name(), outChan)
			currRuns++
			if currRuns >= maxRuns {
				for currRuns >= maxRuns {
					select {
					case <-outChan:
						currRuns--
					}
				}
			}
		}
	}
	for currRuns > 0 {
		select {
		case <-outChan:
			currRuns--
		}
	}
	// part 2: merge To get one past and one future
	// create merged maps over maturity groups
	// maxYield, maxYieldstddev,
	// mat, matstdDev,
	// rain, rainstddev
	// coolweather, coolweatherStddev
	// coolweatherWeight, coolweatherWeigthStddev
	// diffDroughtStress, diffDroughtStressStdDev
	p.calcYieldMatDistribution(maxRefNoOverAll, len(sourceFolder))
	// part 2.1 merge, merged maps for all future Climate scenarios per model
	p.mergeFuture(maxRefNoOverAll, len(sourceFolder))
	// part 2.2 merge all future climate scenarios over all merged models
	// part 2.3 merge historical over models
	p.mergeSources(maxRefNoOverAll, len(sourceFolder))

	// iterate over all values to determine max value

	// part 3: generate ascii grids
	waitForNum := 0
	outC := make(chan string)

	sidebarLabel := make([]string, len(p.matGroupIDGrids)+1)
	colorList := []string{"lightgrey", "maroon", "orangered", "gold", "limegreen", "blue", "mediumorchid"}

	for id := range p.matGroupIDGrids {
		sidebarLabel[p.matGroupIDGrids[id]] = id
	}
	ticklist := []float64{0, 3, 7, 11}
	ticklist = make([]float64, len(sidebarLabel))
	for tick := 0; tick < len(ticklist); tick++ {
		ticklist[tick] = float64(tick) + 0.5
	}
	minColor := "lightgrey"
	// debug
	// waitForNum++
	// go drawScenarioPerModelMaps(gridSourceLookup,
	// 	p.maxYieldGrids,
	// 	"%s_%s_%s_trno%s.asc",
	// 	"max_yield",
	// 	numSourceFolder,
	// 	extCol, extRow,
	// 	asciiOutFolder,
	// 	"Max Yield: %v %v",
	// 	"Yield in t",
	// 	"inferno",
	// 	nil, nil, 0.001, NONEVALUE,
	// 	int(p.maxAllAvgYield), outC)

	// waitForNum++
	// go drawScenarioPerModelMaps(gridSourceLookup,
	// 	p.matGroupGrids,
	// 	"%s_%s_%s_trno%s.asc",
	// 	"matgroups",
	// 	numSourceFolder,
	// 	extCol, extRow,
	// 	asciiOutFolder,
	// 	"matgroups: %v %v",
	// 	"average over 30 years",
	// 	"inferno",
	// 	sidebarLabel, ticklist, 1.0, NONEVALUE,
	// 	len(p.matGroupIDGrids), outC)

	// recalulate max values
	p.setMaxAllAvgYield(float64(findMaxValueInScenarioList(p.maxYieldGridsAll, p.maxYieldDeviationGridsAll)))
	p.setSumMaxDeathOccurrence(findMaxValueInScenarioList(p.coolweatherDeathGridsAll, p.coolweatherDeathDeviationGridsAll))
	// map of max yield average(30y) over all models and maturity groups
	waitForNum++
	go drawScenarioMaps(gridSourceLookup,
		p.maxYieldGridsAll,
		asciiOutTemplate,
		"max_yield",
		extCol, extRow,
		filepath.Join(asciiOutFolder, "max"),
		"Max Yield: %v %v",
		"Yield in t",
		"viridis",
		nil, nil, 0.001, NONEVALUE,
		int(p.maxAllAvgYield), minColor, outC)

	// map of max yield average(30y) over all models and maturity groups with acceptable variation
	waitForNum++
	go drawScenarioMaps(gridSourceLookup,
		p.maxYieldDeviationGridsAll,
		asciiOutTemplate,
		"dev_max_yield",
		extCol, extRow,
		filepath.Join(asciiOutFolder, "dev"),
		"(Dev )Max Yield: %v %v",
		"Yield in t",
		"viridis",
		nil, nil, 0.001, NONEVALUE,
		int(p.maxAllAvgYield), minColor, outC)

	waitForNum++
	go drawScenarioMaps(gridSourceLookup,
		p.coolweatherDeathDeviationGridsAll,
		asciiOutTemplate,
		"dev_cool_weather_severity",
		extCol, extRow,
		filepath.Join(asciiOutFolder, "dev"),
		"(Dev) Cool weather severity: %v %v",
		"counted occurrences with severity factor",
		"rainbow",
		nil, nil, 0.0001, -1,
		p.sumMaxDeathOccurrence, minColor, outC)
	waitForNum++
	go drawScenarioMaps(gridSourceLookup,
		p.coolweatherDeathGridsAll,
		asciiOutTemplate,
		"cool_weather_severity",
		extCol, extRow,
		filepath.Join(asciiOutFolder, "max"),
		"Cool weather severity: %v %v",
		"counted occurrences with severity factor",
		"rainbow",
		nil, nil, 0.0001, -1,
		p.sumMaxDeathOccurrence, minColor, outC)
	waitForNum++
	go drawScenarioMaps(gridSourceLookup,
		p.harvestRainGridsAll,
		asciiOutTemplate,
		"harvest_rain",
		extCol, extRow,
		filepath.Join(asciiOutFolder, "max"),
		"Rain during/before harvest: %v %v",
		"counted occurrences in 30 years",
		"plasma",
		nil, nil, 1.0,
		-1, 2, minColor, outC)

	waitForNum++
	go drawScenarioMaps(gridSourceLookup,
		p.harvestRainDeviationGridsAll,
		asciiOutTemplate,
		"dev_harvest_rain",
		extCol, extRow,
		filepath.Join(asciiOutFolder, "dev"),
		"(Dev) Rain during/before harvest: %v %v",
		"counted occurrences in 30 years",
		"plasma",
		nil, nil, 1.0,
		-1, 2, minColor, outC)
	waitForNum++

	maxPot := findMaxValueInDic(p.potentialWaterStressAll, p.potentialWaterStressDeviationGridsAll)
	go drawMaps(gridSourceLookup,
		p.potentialWaterStressAll,
		asciiOutCombinedTemplate,
		"drought_stress",
		extCol, extRow,
		filepath.Join(asciiOutFolder, "max"),
		"drought stress effect: %v",
		"average yield loss to drought",
		"plasma",
		nil, nil, 1.0, -1,
		maxPot, minColor, outC)
	waitForNum++
	go drawMaps(gridSourceLookup,
		p.potentialWaterStressDeviationGridsAll,
		asciiOutCombinedTemplate,
		"dev_drought_stress",
		extCol, extRow,
		filepath.Join(asciiOutFolder, "dev"),
		"(Dev) drought stress effect: %v",
		"average yield loss to drought",
		"plasma",
		nil, nil, 1.0, -1,
		maxPot, minColor, outC)

	waitForNum++
	go drawMaps(gridSourceLookup,
		p.signDroughtYieldLossDeviationGridsAll,
		asciiOutCombinedTemplate,
		"dev_yield_loss_drought",
		extCol, extRow,
		filepath.Join(asciiOutFolder, "dev"),
		"(Dev) yield loss drought: %v",
		"potential loss steps",
		"plasma",
		nil, nil, 1.0,
		-1, 2, minColor, outC)

	waitForNum++
	go drawMaps(gridSourceLookup,
		p.signDroughtYieldLossGridsAll,
		asciiOutCombinedTemplate,
		"yield_loss_drought",
		extCol, extRow,
		filepath.Join(asciiOutFolder, "max"),
		"yield loss drought: %v",
		"potential loss steps",
		"plasma",
		nil, nil, 1.0, -1,
		2, minColor, outC)

	for waitForNum > 0 {
		select {
		case progessStatus := <-outC:
			waitForNum--
			fmt.Println(progessStatus)
		}
	}

	// generate pictures with maturity groups
	for scenarioKey, scenarioVal := range p.matGroupGridsAll {
		gridFileName := fmt.Sprintf(asciiOutTemplate, "maturity_groups", climateScenarioShortToName(scenarioKey.climateSenario), scenarioKey.treatNo)
		gridFilePath := filepath.Join(asciiOutFolder, "max", gridFileName)

		// create ascii file
		file := writeAGridHeader(gridFilePath, extCol, extRow)
		writeRows(file, extRow, extCol, scenarioVal, gridSourceLookup)
		file.Close()
		// create meta description
		title := fmt.Sprintf("Maturity groups for max average yield: %s %s", climateScenarioShortToName(scenarioKey.climateSenario), scenarioKey.comment)
		writeMetaFile(gridFilePath, title, "Maturity Group", "", colorList, sidebarLabel, ticklist, 1.0, len(sidebarLabel)-1, 0, "")
	}

	for scenarioKey, scenarioVal := range p.matGroupDeviationGridsAll {
		gridFileName := fmt.Sprintf(asciiOutTemplate, "dev_maturity_groups", climateScenarioShortToName(scenarioKey.climateSenario), scenarioKey.treatNo)
		gridFilePath := filepath.Join(asciiOutFolder, "dev", gridFileName)

		// create ascii file
		file := writeAGridHeader(gridFilePath, extCol, extRow)
		writeRows(file, extRow, extCol, scenarioVal, gridSourceLookup)
		file.Close()
		// create meta description
		title := fmt.Sprintf("(Dev)Maturity groups for max average yield: %s %s", climateScenarioShortToName(scenarioKey.climateSenario), scenarioKey.comment)
		writeMetaFile(gridFilePath, title, "Maturity Group", "", colorList, sidebarLabel, ticklist, 1.0, len(sidebarLabel)-1, 0, "")
	}
}

// ProcessedData combined data from results
type ProcessedData struct {
	maxAllAvgYield              float64
	maxSdtDeviation             float64
	allYieldGrids               map[SimKeyTuple][][]int
	StdDevAvgGrids              map[SimKeyTuple][][]int
	harvestGrid                 map[SimKeyTuple][][]int
	matIsHavestGrid             map[SimKeyTuple][][]int
	lateHarvestGrid             map[SimKeyTuple][][]int
	climateFilePeriod           map[string]string
	coolWeatherImpactGrid       map[SimKeyTuple][][]int
	coolWeatherDeathGrid        map[SimKeyTuple][][]int
	coolWeatherImpactWeightGrid map[SimKeyTuple][][]int
	wetHarvestGrid              map[SimKeyTuple][][]int
	sumMaxOccurrence            int
	sumMaxDeathOccurrence       int
	maxLateHarvest              int
	maxWetHarvest               int
	maxMatHarvest               int
	sumLowOccurrence            int
	sumMediumOccurrence         int
	sumHighOccurrence           int
	matGroupIDGrids             map[string]int

	maxYieldGrids                      map[ScenarioKeyTuple][][]int
	matGroupGrids                      map[ScenarioKeyTuple][][]int
	maxYieldDeviationGrids             map[ScenarioKeyTuple][][]int
	matGroupDeviationGrids             map[ScenarioKeyTuple][][]int
	harvestRainGrids                   map[ScenarioKeyTuple][][]int
	harvestRainDeviationGrids          map[ScenarioKeyTuple][][]int
	coolweatherDeathGrids              map[ScenarioKeyTuple][][]int
	coolweatherDeathDeviationGrids     map[ScenarioKeyTuple][][]int
	potentialWaterStress               map[string][][]int
	potentialWaterStressDeviationGrids map[string][][]int

	signDroughtYieldLossGrids          map[string][][]int
	signDroughtYieldLossDeviationGrids map[string][][]int

	maxYieldGridsAll                      map[ScenarioKeyTuple][]int
	matGroupGridsAll                      map[ScenarioKeyTuple][]int
	maxYieldDeviationGridsAll             map[ScenarioKeyTuple][]int
	matGroupDeviationGridsAll             map[ScenarioKeyTuple][]int
	harvestRainGridsAll                   map[ScenarioKeyTuple][]int
	harvestRainDeviationGridsAll          map[ScenarioKeyTuple][]int
	coolweatherDeathGridsAll              map[ScenarioKeyTuple][]int
	coolweatherDeathDeviationGridsAll     map[ScenarioKeyTuple][]int
	potentialWaterStressAll               map[string][]int
	potentialWaterStressDeviationGridsAll map[string][]int

	signDroughtYieldLossGridsAll          map[string][]int
	signDroughtYieldLossDeviationGridsAll map[string][]int

	deviationClimateScenarios map[ScenarioKeyTuple][][]int
	outputGridsGenerated      bool
	mux                       sync.Mutex
}

func (p *ProcessedData) initProcessedData() {
	p.maxAllAvgYield = 0.0
	p.maxSdtDeviation = 0.0
	p.allYieldGrids = make(map[SimKeyTuple][][]int)
	p.StdDevAvgGrids = make(map[SimKeyTuple][][]int)
	p.harvestGrid = make(map[SimKeyTuple][][]int)
	p.matIsHavestGrid = make(map[SimKeyTuple][][]int)
	p.lateHarvestGrid = make(map[SimKeyTuple][][]int)
	p.climateFilePeriod = make(map[string]string)
	p.coolWeatherImpactGrid = make(map[SimKeyTuple][][]int)
	p.coolWeatherDeathGrid = make(map[SimKeyTuple][][]int)
	p.coolWeatherImpactWeightGrid = make(map[SimKeyTuple][][]int)
	p.wetHarvestGrid = make(map[SimKeyTuple][][]int)
	p.sumMaxOccurrence = 0
	p.sumMaxDeathOccurrence = 0
	p.maxLateHarvest = 0
	p.maxWetHarvest = 0
	p.maxMatHarvest = 0
	p.sumLowOccurrence = 0
	p.sumMediumOccurrence = 0
	p.sumHighOccurrence = 0
	p.outputGridsGenerated = false

	p.matGroupIDGrids = map[string]int{
		"none":         0,
		"soybean/II":   1,
		"soybean/I":    2,
		"soybean/0":    3,
		"soybean/00":   4,
		"soybean/000":  5,
		"soybean/0000": 6}
	p.maxYieldGrids = make(map[ScenarioKeyTuple][][]int)
	p.matGroupGrids = make(map[ScenarioKeyTuple][][]int)
	p.maxYieldDeviationGrids = make(map[ScenarioKeyTuple][][]int)
	p.matGroupDeviationGrids = make(map[ScenarioKeyTuple][][]int)

	p.harvestRainGrids = make(map[ScenarioKeyTuple][][]int)
	p.harvestRainDeviationGrids = make(map[ScenarioKeyTuple][][]int)
	p.coolweatherDeathGrids = make(map[ScenarioKeyTuple][][]int)
	p.coolweatherDeathDeviationGrids = make(map[ScenarioKeyTuple][][]int)
	p.potentialWaterStress = make(map[string][][]int)
	p.potentialWaterStressDeviationGrids = make(map[string][][]int)
	p.signDroughtYieldLossGrids = make(map[string][][]int)
	p.signDroughtYieldLossDeviationGrids = make(map[string][][]int)
	p.deviationClimateScenarios = make(map[ScenarioKeyTuple][][]int)

	p.maxYieldGridsAll = make(map[ScenarioKeyTuple][]int)
	p.matGroupGridsAll = make(map[ScenarioKeyTuple][]int)
	p.maxYieldDeviationGridsAll = make(map[ScenarioKeyTuple][]int)
	p.matGroupDeviationGridsAll = make(map[ScenarioKeyTuple][]int)

	p.harvestRainGridsAll = make(map[ScenarioKeyTuple][]int)
	p.harvestRainDeviationGridsAll = make(map[ScenarioKeyTuple][]int)

	p.coolweatherDeathGridsAll = make(map[ScenarioKeyTuple][]int)
	p.coolweatherDeathDeviationGridsAll = make(map[ScenarioKeyTuple][]int)
	p.potentialWaterStressAll = make(map[string][]int)
	p.potentialWaterStressDeviationGridsAll = make(map[string][]int)
	p.signDroughtYieldLossGridsAll = make(map[string][]int)
	p.signDroughtYieldLossDeviationGridsAll = make(map[string][]int)
}

func findMaxValueInScenarioList(lists ...map[ScenarioKeyTuple][]int) int {
	var maxVal int
	for _, list := range lists {
		for _, listVal := range list {
			for _, val := range listVal {
				if val > maxVal {
					maxVal = val
				}
			}
		}
	}
	return maxVal
}

func findMaxValueInDic(lists ...map[string][]int) int {
	var maxVal int
	for _, list := range lists {
		for _, listVal := range list {
			for _, val := range listVal {
				if val > maxVal {
					maxVal = val
				}
			}
		}
	}
	return maxVal
}

func (p *ProcessedData) mergeFuture(maxRefNo, numSource int) {
	// create a new key for summarized future events
	futureScenarioAvgKey := "fut_avg"
	isFuture := func(simKey ScenarioKeyTuple) bool {
		return simKey.climateSenario != "0_0"
	}
	futureKeys := make(map[TreatmentKeyTuple][]ScenarioKeyTuple, 2)
	for simKey := range p.maxYieldGrids {
		if isFuture(simKey) {
			fKey := TreatmentKeyTuple{comment: simKey.comment,
				treatNo: simKey.treatNo}

			if _, ok := futureKeys[fKey]; !ok {
				futureKeys[fKey] = make([]ScenarioKeyTuple, 0, 5)
			}
			futureKeys[fKey] = append(futureKeys[fKey], simKey)
		}
	}

	// summarize potential water stress over all climate scenarios
	p.potentialWaterStress[futureScenarioAvgKey] = newGridLookup(numSource, maxRefNo, 0)
	p.potentialWaterStressDeviationGrids[futureScenarioAvgKey] = newGridLookup(numSource, maxRefNo, 0)
	p.signDroughtYieldLossGrids[futureScenarioAvgKey] = newGridLookup(numSource, maxRefNo, 0)
	p.signDroughtYieldLossDeviationGrids[futureScenarioAvgKey] = newGridLookup(numSource, maxRefNo, 0)

	numScenKey := len(p.potentialWaterStress)
	for sIdx := 0; sIdx < numSource; sIdx++ {
		for rIdx := 0; rIdx < maxRefNo; rIdx++ {
			for climateScenario := range p.potentialWaterStress {
				p.potentialWaterStress[futureScenarioAvgKey][sIdx][rIdx] = p.potentialWaterStress[futureScenarioAvgKey][sIdx][rIdx] + p.potentialWaterStress[climateScenario][sIdx][rIdx]
				p.potentialWaterStressDeviationGrids[futureScenarioAvgKey][sIdx][rIdx] = p.potentialWaterStressDeviationGrids[futureScenarioAvgKey][sIdx][rIdx] + p.potentialWaterStressDeviationGrids[climateScenario][sIdx][rIdx]
				p.signDroughtYieldLossGrids[futureScenarioAvgKey][sIdx][rIdx] = p.signDroughtYieldLossGrids[futureScenarioAvgKey][sIdx][rIdx] + p.signDroughtYieldLossGrids[climateScenario][sIdx][rIdx]
				p.signDroughtYieldLossDeviationGrids[futureScenarioAvgKey][sIdx][rIdx] = p.signDroughtYieldLossDeviationGrids[futureScenarioAvgKey][sIdx][rIdx] + p.signDroughtYieldLossDeviationGrids[climateScenario][sIdx][rIdx]
			}

			p.potentialWaterStress[futureScenarioAvgKey][sIdx][rIdx] = p.potentialWaterStress[futureScenarioAvgKey][sIdx][rIdx] / numScenKey
			p.potentialWaterStressDeviationGrids[futureScenarioAvgKey][sIdx][rIdx] = p.potentialWaterStressDeviationGrids[futureScenarioAvgKey][sIdx][rIdx] / numScenKey
			p.signDroughtYieldLossGrids[futureScenarioAvgKey][sIdx][rIdx] = p.signDroughtYieldLossGrids[futureScenarioAvgKey][sIdx][rIdx] / numScenKey
			p.signDroughtYieldLossDeviationGrids[futureScenarioAvgKey][sIdx][rIdx] = p.signDroughtYieldLossDeviationGrids[futureScenarioAvgKey][sIdx][rIdx] / numScenKey
		}
	}

	for mergeTreatmentKey, scenariokeys := range futureKeys {
		// make a simKey for sumarized future
		futureSimKey := ScenarioKeyTuple{
			climateSenario: futureScenarioAvgKey,
			comment:        mergeTreatmentKey.comment,
			treatNo:        mergeTreatmentKey.treatNo,
		}

		p.maxYieldGrids[futureSimKey] = newGridLookup(numSource, maxRefNo, 0)
		p.matGroupGrids[futureSimKey] = newGridLookup(numSource, maxRefNo, 0)
		p.maxYieldDeviationGrids[futureSimKey] = newGridLookup(numSource, maxRefNo, 0)
		p.matGroupDeviationGrids[futureSimKey] = newGridLookup(numSource, maxRefNo, 0)
		p.harvestRainGrids[futureSimKey] = newGridLookup(numSource, maxRefNo, -1)
		p.harvestRainDeviationGrids[futureSimKey] = newGridLookup(numSource, maxRefNo, -1)
		p.coolweatherDeathGrids[futureSimKey] = newGridLookup(numSource, maxRefNo, -1)
		p.coolweatherDeathDeviationGrids[futureSimKey] = newGridLookup(numSource, maxRefNo, -1)
		p.deviationClimateScenarios[futureSimKey] = newGridLookup(numSource, maxRefNo, 0)

		for sIdx := 0; sIdx < numSource; sIdx++ {
			for rIdx := 0; rIdx < maxRefNo; rIdx++ {
				numSimKey := len(scenariokeys)
				stdDevClimScen := make([]float64, numSimKey) // standard deviation over yield
				numharvestRainGrids := 0
				numharvestRainDeviationGrids := 0
				numcoolweatherDeathGrids := 0
				numcoolweatherDeathDeviationGrids := 0
				matGroupClimDistribution := make([]int, numSimKey)
				matGroupDevClimDistribution := make([]int, numSimKey)

				for i, scenariokey := range scenariokeys {

					stdDevClimScen[i] = float64(p.maxYieldGrids[scenariokey][sIdx][rIdx])
					p.maxYieldGrids[futureSimKey][sIdx][rIdx] = p.maxYieldGrids[futureSimKey][sIdx][rIdx] + p.maxYieldGrids[scenariokey][sIdx][rIdx]
					p.maxYieldDeviationGrids[futureSimKey][sIdx][rIdx] = p.maxYieldDeviationGrids[futureSimKey][sIdx][rIdx] + p.maxYieldDeviationGrids[scenariokey][sIdx][rIdx]

					matGroupClimDistribution[i] = p.matGroupGrids[scenariokey][sIdx][rIdx]
					matGroupDevClimDistribution[i] = p.matGroupDeviationGrids[scenariokey][sIdx][rIdx]

					// below 0 means no data
					if p.harvestRainGrids[scenariokey][sIdx][rIdx] >= 0 {
						numharvestRainGrids++
						if p.harvestRainGrids[futureSimKey][sIdx][rIdx] < 0 {
							p.harvestRainGrids[futureSimKey][sIdx][rIdx] = 0
						}
						p.harvestRainGrids[futureSimKey][sIdx][rIdx] = p.harvestRainGrids[futureSimKey][sIdx][rIdx] + p.harvestRainGrids[scenariokey][sIdx][rIdx]
					}
					if p.harvestRainDeviationGrids[scenariokey][sIdx][rIdx] >= 0 {
						numharvestRainDeviationGrids++
						if p.harvestRainDeviationGrids[futureSimKey][sIdx][rIdx] < 0 {
							p.harvestRainDeviationGrids[futureSimKey][sIdx][rIdx] = 0
						}
						p.harvestRainDeviationGrids[futureSimKey][sIdx][rIdx] = p.harvestRainDeviationGrids[futureSimKey][sIdx][rIdx] + p.harvestRainDeviationGrids[scenariokey][sIdx][rIdx]
					}
					if p.coolweatherDeathGrids[scenariokey][sIdx][rIdx] >= 0 {
						numcoolweatherDeathGrids++
						if p.coolweatherDeathGrids[futureSimKey][sIdx][rIdx] < 0 {
							p.coolweatherDeathGrids[futureSimKey][sIdx][rIdx] = 0
						}
						p.coolweatherDeathGrids[futureSimKey][sIdx][rIdx] = p.coolweatherDeathGrids[futureSimKey][sIdx][rIdx] + p.coolweatherDeathGrids[scenariokey][sIdx][rIdx]
					}
					if p.coolweatherDeathDeviationGrids[scenariokey][sIdx][rIdx] >= 0 {
						numcoolweatherDeathDeviationGrids++
						if p.coolweatherDeathDeviationGrids[futureSimKey][sIdx][rIdx] < 0 {
							p.coolweatherDeathDeviationGrids[futureSimKey][sIdx][rIdx] = 0
						}
						p.coolweatherDeathDeviationGrids[futureSimKey][sIdx][rIdx] = p.coolweatherDeathDeviationGrids[futureSimKey][sIdx][rIdx] + p.coolweatherDeathDeviationGrids[scenariokey][sIdx][rIdx]
					}
				}
				sort.Ints(matGroupClimDistribution)
				sort.Ints(matGroupDevClimDistribution)
				centerIdx := int(float64(numSimKey)/2+0.5) - 1
				p.matGroupGrids[futureSimKey][sIdx][rIdx] = matGroupClimDistribution[centerIdx]
				p.matGroupDeviationGrids[futureSimKey][sIdx][rIdx] = matGroupDevClimDistribution[centerIdx]

				p.deviationClimateScenarios[futureSimKey][sIdx][rIdx] = int(stat.StdDev(stdDevClimScen, nil))
				p.maxYieldGrids[futureSimKey][sIdx][rIdx] = p.maxYieldGrids[futureSimKey][sIdx][rIdx] / numSimKey
				p.maxYieldDeviationGrids[futureSimKey][sIdx][rIdx] = p.maxYieldDeviationGrids[futureSimKey][sIdx][rIdx] / numSimKey
				if numharvestRainGrids > 0 {
					p.harvestRainGrids[futureSimKey][sIdx][rIdx] = p.harvestRainGrids[futureSimKey][sIdx][rIdx] / numharvestRainGrids
				}
				if numharvestRainDeviationGrids > 0 {
					p.harvestRainDeviationGrids[futureSimKey][sIdx][rIdx] = p.harvestRainDeviationGrids[futureSimKey][sIdx][rIdx] / numharvestRainDeviationGrids
				}
				if numcoolweatherDeathGrids > 0 {
					p.coolweatherDeathGrids[futureSimKey][sIdx][rIdx] = p.coolweatherDeathGrids[futureSimKey][sIdx][rIdx] / numcoolweatherDeathGrids
				}
				if numcoolweatherDeathDeviationGrids > 0 {
					p.coolweatherDeathDeviationGrids[futureSimKey][sIdx][rIdx] = p.coolweatherDeathDeviationGrids[futureSimKey][sIdx][rIdx] / numcoolweatherDeathDeviationGrids
				}
			}
		}
	}

}

func (p *ProcessedData) calcYieldMatDistribution(maxRefNo, numSources int) {
	// calculate max yield layer and maturity layer grid
	for simKey, currGrid := range p.allYieldGrids {
		//treatmentNoIdx, climateSenarioIdx, mGroupIdx, commentIdx
		scenarioKey := ScenarioKeyTuple{simKey.treatNo, simKey.climateSenario, simKey.comment}
		if _, ok := p.maxYieldGrids[scenarioKey]; !ok {
			p.maxYieldGrids[scenarioKey] = newGridLookup(numSources, maxRefNo, 0)
			p.matGroupGrids[scenarioKey] = newGridLookup(numSources, maxRefNo, 0)
			p.maxYieldDeviationGrids[scenarioKey] = newGridLookup(numSources, maxRefNo, 0)
			p.matGroupDeviationGrids[scenarioKey] = newGridLookup(numSources, maxRefNo, 0)
		}
		for idx, sourceGrid := range currGrid {

			for ref := 0; ref < maxRefNo; ref++ {
				if sourceGrid[ref] > p.maxYieldGrids[scenarioKey][idx][ref] {
					p.maxYieldGrids[scenarioKey][idx][ref] = sourceGrid[ref]
					p.maxYieldDeviationGrids[scenarioKey][idx][ref] = sourceGrid[ref]
					if sourceGrid[ref] == 0 {
						p.matGroupGrids[scenarioKey][idx][ref] = p.matGroupIDGrids["none"]
						p.matGroupDeviationGrids[scenarioKey][idx][ref] = p.matGroupIDGrids["none"]
					} else {
						p.matGroupGrids[scenarioKey][idx][ref] = p.matGroupIDGrids[simKey.mGroup]
						p.matGroupDeviationGrids[scenarioKey][idx][ref] = p.matGroupIDGrids[simKey.mGroup]
					}
				}
			}
		}
	}
	invMatGroupIDGrids := make(map[int]string, len(p.matGroupIDGrids))
	for k, v := range p.matGroupIDGrids {
		invMatGroupIDGrids[v] = k
	}

	for simKey, currGridYield := range p.allYieldGrids {
		for idx, sourceGrid := range currGridYield {

			//#treatmentNoIdx, climateSenarioIdx, mGroupIdx, CommentIdx
			scenarioKey := ScenarioKeyTuple{simKey.treatNo, simKey.climateSenario, simKey.comment}
			currGridDeviation := p.StdDevAvgGrids[simKey][idx]
			for ref := 0; ref < maxRefNo; ref++ {
				if p.matGroupDeviationGrids[scenarioKey][idx][ref] > 0 {
					matGroup := invMatGroupIDGrids[p.matGroupDeviationGrids[scenarioKey][idx][ref]]
					matGroupKey := SimKeyTuple{simKey.treatNo, simKey.climateSenario, matGroup, simKey.comment}
					if float64(sourceGrid[ref]) > float64(p.maxYieldGrids[scenarioKey][idx][ref])*0.9 &&
						currGridDeviation[ref] < p.StdDevAvgGrids[matGroupKey][idx][ref] {
						p.maxYieldDeviationGrids[scenarioKey][idx][ref] = sourceGrid[ref]
						p.matGroupDeviationGrids[scenarioKey][idx][ref] = p.matGroupIDGrids[simKey.mGroup]
					}
				}
			}
		}
	}
	for scenarioKey, sourcreGrids := range p.matGroupGrids {
		if _, ok := p.harvestRainGrids[scenarioKey]; !ok {
			maxRefNo = len(sourcreGrids[0])
			numSources = len(sourcreGrids)
			p.harvestRainGrids[scenarioKey] = newGridLookup(numSources, maxRefNo, -1)
			p.harvestRainDeviationGrids[scenarioKey] = newGridLookup(numSources, maxRefNo, -1)
			p.coolweatherDeathGrids[scenarioKey] = newGridLookup(numSources, maxRefNo, -1)
			p.coolweatherDeathDeviationGrids[scenarioKey] = newGridLookup(numSources, maxRefNo, -1)
		}

		for sourceID, sourceGrid := range sourcreGrids {
			for ref := 0; ref < maxRefNo; ref++ {
				if sourceGrid[ref] > 0 {
					matGroup := invMatGroupIDGrids[sourceGrid[ref]]
					matGroupKey := SimKeyTuple{scenarioKey.treatNo, scenarioKey.climateSenario, matGroup, scenarioKey.comment}
					p.harvestRainGrids[scenarioKey][sourceID][ref] = p.wetHarvestGrid[matGroupKey][sourceID][ref]
					p.coolweatherDeathGrids[scenarioKey][sourceID][ref] = p.coolWeatherDeathGrid[matGroupKey][sourceID][ref]
				}

				if p.matGroupDeviationGrids[scenarioKey][sourceID][ref] > 0 {
					matGroupDev := invMatGroupIDGrids[p.matGroupDeviationGrids[scenarioKey][sourceID][ref]]
					matGroupDevKey := SimKeyTuple{scenarioKey.treatNo, scenarioKey.climateSenario, matGroupDev, scenarioKey.comment}
					p.harvestRainDeviationGrids[scenarioKey][sourceID][ref] = p.wetHarvestGrid[matGroupDevKey][sourceID][ref]
					p.coolweatherDeathDeviationGrids[scenarioKey][sourceID][ref] = p.coolWeatherDeathGrid[matGroupDevKey][sourceID][ref]
				}
			}
		}
		for scenarioKey, simValue := range p.maxYieldGrids {
			// treatment number
			if scenarioKey.treatNo == "T1" {
				otherKey := ScenarioKeyTuple{"T2", scenarioKey.climateSenario, "Unlimited water"}
				newDiffGrid := gridDifference(p.maxYieldGrids[otherKey], simValue, maxRefNo)
				p.potentialWaterStress[scenarioKey.climateSenario] = newDiffGrid

				signDiffGrid := gridSignDifference(p.maxYieldGrids[otherKey], simValue, maxRefNo)
				p.signDroughtYieldLossGrids[scenarioKey.climateSenario] = signDiffGrid
			}
		}
		for scenarioKey, simValue := range p.maxYieldDeviationGrids {
			// treatment number
			if scenarioKey.treatNo == "T1" {
				otherKey := ScenarioKeyTuple{"T2", scenarioKey.climateSenario, "Unlimited water"}
				newDiffGrid := gridDifference(p.maxYieldDeviationGrids[otherKey], simValue, maxRefNo)
				p.potentialWaterStressDeviationGrids[scenarioKey.climateSenario] = newDiffGrid

				signDiffGrid := gridSignDifference(p.maxYieldDeviationGrids[otherKey], simValue, maxRefNo)
				p.signDroughtYieldLossDeviationGrids[scenarioKey.climateSenario] = signDiffGrid
			}
		}
	}
}

func (p *ProcessedData) mergeSources(maxRefNo, numSource int) {
	// create a new key for summarized future events
	isFuture := func(simKey ScenarioKeyTuple) bool {
		return simKey.climateSenario == "fut_avg"
	}
	isHistorical := func(simKey ScenarioKeyTuple) bool {
		return simKey.climateSenario == "0_0"
	}
	mergedKeys := make([]ScenarioKeyTuple, 0, 4)
	for simKey := range p.maxYieldGrids {
		if isFuture(simKey) || isHistorical(simKey) {
			mergedKeys = append(mergedKeys, simKey)
		}
	}
	for _, mergedKey := range mergedKeys {

		if _, ok := p.maxYieldGridsAll[mergedKey]; !ok {
			p.maxYieldGridsAll[mergedKey] = newSmallGridLookup(maxRefNo, 0)
			p.matGroupGridsAll[mergedKey] = newSmallGridLookup(maxRefNo, 0)
			p.maxYieldDeviationGridsAll[mergedKey] = newSmallGridLookup(maxRefNo, 0)
			p.matGroupDeviationGridsAll[mergedKey] = newSmallGridLookup(maxRefNo, 0)
			p.harvestRainGridsAll[mergedKey] = newSmallGridLookup(maxRefNo, -1)
			p.harvestRainDeviationGridsAll[mergedKey] = newSmallGridLookup(maxRefNo, -1)
			p.coolweatherDeathGridsAll[mergedKey] = newSmallGridLookup(maxRefNo, -1)
			p.coolweatherDeathDeviationGridsAll[mergedKey] = newSmallGridLookup(maxRefNo, -1)
			p.potentialWaterStressAll[mergedKey.climateSenario] = newSmallGridLookup(maxRefNo, -1)
			p.potentialWaterStressDeviationGridsAll[mergedKey.climateSenario] = newSmallGridLookup(maxRefNo, -1)
			p.signDroughtYieldLossGridsAll[mergedKey.climateSenario] = newSmallGridLookup(maxRefNo, 0)
			p.signDroughtYieldLossDeviationGridsAll[mergedKey.climateSenario] = newSmallGridLookup(maxRefNo, 0)
		}
		matGroupDistribution := make([]int, numSource)
		matGroupDevDistribution := make([]int, numSource)

		for rIdx := 0; rIdx < maxRefNo; rIdx++ {

			numharvestRainGrids := 0
			numharvestRainDeviationGrids := 0
			numcoolweatherDeathGrids := 0
			numcoolweatherDeathDeviationGrids := 0

			for sIdx := 0; sIdx < numSource; sIdx++ {

				matGroupDistribution[sIdx] = p.matGroupGrids[mergedKey][sIdx][rIdx]
				matGroupDevDistribution[sIdx] = p.matGroupDeviationGrids[mergedKey][sIdx][rIdx]

				p.maxYieldGridsAll[mergedKey][rIdx] = p.maxYieldGridsAll[mergedKey][rIdx] + p.maxYieldGrids[mergedKey][sIdx][rIdx]
				p.maxYieldDeviationGridsAll[mergedKey][rIdx] = p.maxYieldDeviationGridsAll[mergedKey][rIdx] + p.maxYieldDeviationGrids[mergedKey][sIdx][rIdx]

				// below 0 means no data
				if p.harvestRainGrids[mergedKey][sIdx][rIdx] >= 0 {
					numharvestRainGrids++
					if p.harvestRainGridsAll[mergedKey][rIdx] < 0 {
						p.harvestRainGridsAll[mergedKey][rIdx] = 0
					}
					p.harvestRainGridsAll[mergedKey][rIdx] = p.harvestRainGridsAll[mergedKey][rIdx] + p.harvestRainGrids[mergedKey][sIdx][rIdx]
				}
				if p.harvestRainDeviationGrids[mergedKey][sIdx][rIdx] >= 0 {
					numharvestRainDeviationGrids++
					if p.harvestRainDeviationGridsAll[mergedKey][rIdx] < 0 {
						p.harvestRainDeviationGridsAll[mergedKey][rIdx] = 0
					}
					p.harvestRainDeviationGridsAll[mergedKey][rIdx] = p.harvestRainDeviationGridsAll[mergedKey][rIdx] + p.harvestRainDeviationGrids[mergedKey][sIdx][rIdx]
				}
				if p.coolweatherDeathGrids[mergedKey][sIdx][rIdx] >= 0 {
					numcoolweatherDeathGrids++
					if p.coolweatherDeathGridsAll[mergedKey][rIdx] < 0 {
						p.coolweatherDeathGridsAll[mergedKey][rIdx] = 0
					}
					p.coolweatherDeathGridsAll[mergedKey][rIdx] = p.coolweatherDeathGridsAll[mergedKey][rIdx] + p.coolweatherDeathGrids[mergedKey][sIdx][rIdx]
				}
				if p.coolweatherDeathDeviationGrids[mergedKey][sIdx][rIdx] >= 0 {
					numcoolweatherDeathDeviationGrids++
					if p.coolweatherDeathDeviationGridsAll[mergedKey][rIdx] < 0 {
						p.coolweatherDeathDeviationGridsAll[mergedKey][rIdx] = 0
					}
					p.coolweatherDeathDeviationGridsAll[mergedKey][rIdx] = p.coolweatherDeathDeviationGridsAll[mergedKey][rIdx] + p.coolweatherDeathDeviationGrids[mergedKey][sIdx][rIdx]
				}

				p.potentialWaterStressAll[mergedKey.climateSenario][rIdx] = p.potentialWaterStressAll[mergedKey.climateSenario][rIdx] + p.potentialWaterStress[mergedKey.climateSenario][sIdx][rIdx]
				p.potentialWaterStressDeviationGridsAll[mergedKey.climateSenario][rIdx] = p.potentialWaterStressDeviationGridsAll[mergedKey.climateSenario][rIdx] + p.potentialWaterStressDeviationGrids[mergedKey.climateSenario][sIdx][rIdx]

				p.signDroughtYieldLossGridsAll[mergedKey.climateSenario][rIdx] = p.signDroughtYieldLossGridsAll[mergedKey.climateSenario][rIdx] + p.signDroughtYieldLossGrids[mergedKey.climateSenario][sIdx][rIdx]
				p.signDroughtYieldLossDeviationGridsAll[mergedKey.climateSenario][rIdx] = p.signDroughtYieldLossDeviationGridsAll[mergedKey.climateSenario][rIdx] + p.signDroughtYieldLossDeviationGrids[mergedKey.climateSenario][sIdx][rIdx]
			}

			sort.Ints(matGroupDistribution)
			sort.Ints(matGroupDevDistribution)
			centerIdx := int(float64(numSource)/2+0.5) - 1
			p.matGroupGridsAll[mergedKey][rIdx] = matGroupDistribution[centerIdx]
			p.matGroupDeviationGridsAll[mergedKey][rIdx] = matGroupDevDistribution[centerIdx]

			p.maxYieldGridsAll[mergedKey][rIdx] = p.maxYieldGridsAll[mergedKey][rIdx] / numSource
			p.maxYieldDeviationGridsAll[mergedKey][rIdx] = p.maxYieldDeviationGridsAll[mergedKey][rIdx] / numSource
			if numharvestRainGrids > 0 {
				p.harvestRainGridsAll[mergedKey][rIdx] = p.harvestRainGridsAll[mergedKey][rIdx] / numharvestRainGrids
				if p.harvestRainGridsAll[mergedKey][rIdx] > 3 {
					p.harvestRainGridsAll[mergedKey][rIdx] = 1
				} else {
					p.harvestRainGridsAll[mergedKey][rIdx] = 0
				}
			}
			if numharvestRainDeviationGrids > 0 {
				p.harvestRainDeviationGridsAll[mergedKey][rIdx] = p.harvestRainDeviationGridsAll[mergedKey][rIdx] / numharvestRainDeviationGrids
				if p.harvestRainDeviationGridsAll[mergedKey][rIdx] > 3 {
					p.harvestRainDeviationGridsAll[mergedKey][rIdx] = 1
				} else {
					p.harvestRainDeviationGridsAll[mergedKey][rIdx] = 0
				}
			}
			if numcoolweatherDeathGrids > 0 {
				p.coolweatherDeathGridsAll[mergedKey][rIdx] = p.coolweatherDeathGridsAll[mergedKey][rIdx] / numcoolweatherDeathGrids
			}
			if numcoolweatherDeathDeviationGrids > 0 {
				p.coolweatherDeathDeviationGridsAll[mergedKey][rIdx] = p.coolweatherDeathDeviationGridsAll[mergedKey][rIdx] / numcoolweatherDeathDeviationGrids
			}
			p.potentialWaterStressAll[mergedKey.climateSenario][rIdx] = p.potentialWaterStressAll[mergedKey.climateSenario][rIdx] / numSource
			p.potentialWaterStressDeviationGridsAll[mergedKey.climateSenario][rIdx] = p.potentialWaterStressDeviationGridsAll[mergedKey.climateSenario][rIdx] / numSource

			p.signDroughtYieldLossGridsAll[mergedKey.climateSenario][rIdx] = p.signDroughtYieldLossGridsAll[mergedKey.climateSenario][rIdx] / numSource
			p.signDroughtYieldLossDeviationGridsAll[mergedKey.climateSenario][rIdx] = p.signDroughtYieldLossDeviationGridsAll[mergedKey.climateSenario][rIdx] / numSource

		}
	}
}

func (p *ProcessedData) setClimateFilePeriod(climateSenario, period string) {
	p.mux.Lock()
	if _, ok := p.climateFilePeriod[climateSenario]; !ok {
		p.climateFilePeriod[climateSenario] = period
	}
	p.mux.Unlock()
}
func (p *ProcessedData) setMaxAllAvgYield(pixelValue float64) {
	p.mux.Lock()
	if pixelValue > p.maxAllAvgYield {
		p.maxAllAvgYield = pixelValue
	}
	p.mux.Unlock()
}
func (p *ProcessedData) setMaxSdtDeviation(stdDeviation float64) {
	p.mux.Lock()
	if stdDeviation > p.maxSdtDeviation {
		p.maxSdtDeviation = stdDeviation
	}
	p.mux.Unlock()
}
func (p *ProcessedData) setMaxLateHarvest(val int) {
	p.mux.Lock()
	if p.maxLateHarvest < val {
		p.maxLateHarvest = val
	}
	p.mux.Unlock()
}
func (p *ProcessedData) setMaxMatHarvest(val int) {
	p.mux.Lock()
	if p.maxMatHarvest < val {
		p.maxMatHarvest = val
	}
	p.mux.Unlock()
}
func (p *ProcessedData) setSumLowOccurrence(val int) {
	p.mux.Lock()
	if p.sumLowOccurrence < val {
		p.sumLowOccurrence = val
	}
	p.mux.Unlock()
}
func (p *ProcessedData) setSumMediumOccurrence(val int) {
	p.mux.Lock()
	if p.sumMediumOccurrence < val {
		p.sumMediumOccurrence = val
	}
	p.mux.Unlock()
}
func (p *ProcessedData) setSumHighOccurrence(val int) {
	p.mux.Lock()
	if p.sumHighOccurrence < val {
		p.sumHighOccurrence = val
	}
	p.mux.Unlock()
}
func (p *ProcessedData) setSumMaxOccurrence(sumOccurrence int) {
	p.mux.Lock()
	if p.sumMaxOccurrence < sumOccurrence {
		p.sumMaxOccurrence = sumOccurrence
	}
	p.mux.Unlock()
}
func (p *ProcessedData) setSumMaxDeathOccurrence(sumDeathOccurrence int) {
	p.mux.Lock()
	if p.sumMaxDeathOccurrence < sumDeathOccurrence {
		p.sumMaxDeathOccurrence = sumDeathOccurrence
	}
	p.mux.Unlock()
}
func (p *ProcessedData) setMaxWetHarvest(val int) {
	p.mux.Lock()
	if p.maxWetHarvest < val {
		p.maxWetHarvest = val
	}
	p.mux.Unlock()
}
func (p *ProcessedData) setOutputGridsGenerated(simulations map[SimKeyTuple][]float64, numSoures, maxRefNo int) bool {

	p.mux.Lock()
	out := false
	if !p.outputGridsGenerated {
		p.outputGridsGenerated = true
		out = true
		for simKey := range simulations {
			p.allYieldGrids[simKey] = newGridLookup(numSoures, maxRefNo, 0)
			p.StdDevAvgGrids[simKey] = newGridLookup(numSoures, maxRefNo, 0)
			p.harvestGrid[simKey] = newGridLookup(numSoures, maxRefNo, 0)
			p.matIsHavestGrid[simKey] = newGridLookup(numSoures, maxRefNo, 0)
			p.lateHarvestGrid[simKey] = newGridLookup(numSoures, maxRefNo, 0)
			p.coolWeatherImpactGrid[simKey] = newGridLookup(numSoures, maxRefNo, -100)
			p.coolWeatherDeathGrid[simKey] = newGridLookup(numSoures, maxRefNo, -1)
			p.coolWeatherImpactWeightGrid[simKey] = newGridLookup(numSoures, maxRefNo, -1)
			p.wetHarvestGrid[simKey] = newGridLookup(numSoures, maxRefNo, -1)

		}
	}
	p.mux.Unlock()
	return out
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
	if doy >= startDOY && startDOY > 0 && doy <= endDOY {
		return true
	}
	return false
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

func gridDifference(grid1, grid2 [][]int, maxRef int) [][]int {
	sourceLen := len(grid1)
	// calculate the difference between 2 grids, save it to new grid
	newGridDiff := newGridLookup(sourceLen, maxRef, NONEVALUE)
	for sIdx := 0; sIdx < sourceLen; sIdx++ {
		for ref := 0; ref < maxRef; ref++ {
			if grid1[sIdx][ref] != NONEVALUE && grid2[sIdx][ref] != NONEVALUE {
				newGridDiff[sIdx][ref] = grid1[sIdx][ref] - grid2[sIdx][ref]
				if grid1[sIdx][ref] == 0 {
					newGridDiff[sIdx][ref] = -1
				} else if newGridDiff[sIdx][ref] < 0 {
					newGridDiff[sIdx][ref] = 0
					// effects can be negative, when sufficient water leads to a shift growth dates
					// these are only small effects but cause trouble with rendering
				}
			} else {
				newGridDiff[sIdx][ref] = NONEVALUE
			}
		}
	}
	return newGridDiff
}

func gridSignDifference(grid1, grid2 [][]int, maxRef int) [][]int {
	sourceLen := len(grid1)
	// calculate the difference between 2 grids, save it to new grid
	newGridDiff := newGridLookup(sourceLen, maxRef, NONEVALUE)
	for sIdx := 0; sIdx < sourceLen; sIdx++ {
		for ref := 0; ref < maxRef; ref++ {
			if grid1[sIdx][ref] != NONEVALUE && grid2[sIdx][ref] != NONEVALUE {

				newGridDiff[sIdx][ref] = grid1[sIdx][ref] - grid2[sIdx][ref]
				if grid1[sIdx][ref] == 0 {
					newGridDiff[sIdx][ref] = -1
				} else if newGridDiff[sIdx][ref] > 0 && grid2[sIdx][ref] == 0 {
					newGridDiff[sIdx][ref] = 2
				} else if newGridDiff[sIdx][ref] > grid1[sIdx][ref]/3 {
					newGridDiff[sIdx][ref] = 1
				} else {
					newGridDiff[sIdx][ref] = 0
				}
			} else {
				newGridDiff[sIdx][ref] = NONEVALUE
			}
		}
	}
	return newGridDiff
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

// SimKeyTuple key to identify each simulatio setup
type SimKeyTuple struct {
	treatNo        string
	climateSenario string
	mGroup         string
	comment        string
}

// TreatmentKeyTuple key to identify a setup without climate scenario
type TreatmentKeyTuple struct {
	treatNo string
	comment string
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

//ScenarioKeyTuple ...
type ScenarioKeyTuple struct {
	treatNo        string
	climateSenario string
	comment        string
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
	sowIdx            int
}

// GridCoord tuple of positions
type GridCoord struct {
	row int
	col int
}

func newGridLookup(numSources, maxRef, defaultVal int) [][]int {
	grid := make([][]int, numSources)
	for s := 0; s < numSources; s++ {
		grid[s] = make([]int, maxRef)
		for i := 0; i < maxRef; i++ {
			grid[s][i] = defaultVal
		}
	}
	return grid
}

func newSmallGridLookup(maxRef, defaultVal int) []int {
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

func climateScenarioShortToName(climateScenarioShort string) string {
	if climateScenarioShort == "0_0" {
		return "historical"
	}
	if climateScenarioShort == "fut_avg" {
		return "future"
	}
	// return original by default
	return climateScenarioShort
}

func drawScenarioMaps(gridSourceLookup [][]int, grids map[ScenarioKeyTuple][]int, filenameFormat, filenameDescPart string, extCol, extRow int, asciiOutFolder, titleFormat, labelText string, colormap string, cbarLabel []string, ticklist []float64, factor float64, minVal, maxVal int, minColor string, outC chan string) {

	for simKey, simVal := range grids {
		//simkey = treatmentNo, climateSenario, maturityGroup, comment
		gridFileName := fmt.Sprintf(filenameFormat, filenameDescPart, climateScenarioShortToName(simKey.climateSenario), simKey.treatNo)
		gridFilePath := filepath.Join(asciiOutFolder, gridFileName)
		file := writeAGridHeader(gridFilePath, extCol, extRow)

		writeRows(file, extRow, extCol, simVal, gridSourceLookup)
		file.Close()
		title := fmt.Sprintf(titleFormat, climateScenarioShortToName(simKey.climateSenario), simKey.comment)
		writeMetaFile(gridFilePath, title, labelText, colormap, nil, cbarLabel, ticklist, factor, maxVal, minVal, minColor)

	}
	outC <- filenameDescPart
}

func drawScenarioPerModelMaps(gridSourceLookup [][]int, grids map[ScenarioKeyTuple][][]int, filenameFormat, filenameDescPart string, numsource, extCol, extRow int, asciiOutFolder, titleFormat, labelText string, colormap string, cbarLabel []string, ticklist []float64, factor float64, minVal, maxVal int, minColor string, outC chan string) {

	for i := 0; i < numsource; i++ {
		for simKey, simVal := range grids {
			//simkey = treatmentNo, climateSenario, maturityGroup, comment
			gridFileName := fmt.Sprintf(filenameFormat, strconv.Itoa(i), filenameDescPart, climateScenarioShortToName(simKey.climateSenario), simKey.treatNo)
			gridFilePath := filepath.Join(asciiOutFolder, gridFileName)
			file := writeAGridHeader(gridFilePath, extCol, extRow)

			writeRows(file, extRow, extCol, simVal[i], gridSourceLookup)
			file.Close()
			title := fmt.Sprintf(titleFormat, climateScenarioShortToName(simKey.climateSenario), simKey.comment)
			writeMetaFile(gridFilePath, title, labelText, colormap, nil, cbarLabel, ticklist, factor, maxVal, minVal, minColor)

		}
	}
	outC <- "debug models" + filenameDescPart
}

func drawMaps(gridSourceLookup [][]int, grids map[string][]int, filenameFormat, filenameDescPart string, extCol, extRow int, asciiOutFolder, titleFormat, labelText string, colormap string, cbarLabel []string, ticklist []float64, factor float64, minVal, maxVal int, minColor string, outC chan string) {

	for simKey, simVal := range grids {
		//simkey = treatmentNo, climateSenario, maturityGroup, comment
		gridFileName := fmt.Sprintf(filenameFormat, filenameDescPart, climateScenarioShortToName(simKey))
		gridFilePath := filepath.Join(asciiOutFolder, gridFileName)
		file := writeAGridHeader(gridFilePath, extCol, extRow)

		writeRows(file, extRow, extCol, simVal, gridSourceLookup)
		file.Close()
		title := fmt.Sprintf(titleFormat, climateScenarioShortToName(simKey))
		writeMetaFile(gridFilePath, title, labelText, colormap, nil, cbarLabel, ticklist, factor, maxVal, minVal, minColor)

	}
	outC <- filenameDescPart
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

func writeMetaFile(gridFilePath, title, labeltext, colormap string, colorlist []string, cbarLabel []string, ticklist []float64, factor float64, maxValue, minValue int, minColor string) {
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
	if len(minColor) > 0 {
		file.WriteString(fmt.Sprintf("minColor: %s\n", minColor))
	}
}

func writeRows(fout Fout, extRow, extCol int, simGrid []int, gridSourceLookup [][]int) {
	for row := 0; row < extRow; row++ {

		for col := 0; col < extCol; col++ {
			refID := gridSourceLookup[row][col]
			if refID >= 0 {
				fout.Write(strconv.Itoa(simGrid[refID-1]))
				fout.Write(" ")
			} else {
				fout.Write("-9999 ")
			}
		}
		fout.Write("\n")
	}
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

func makeDir(outPath string) {
	dir := filepath.Dir(outPath)
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		if err := os.MkdirAll(dir, os.ModePerm); err != nil {
			log.Fatalf("ERROR: Failed to generate output path %s :%v", dir, err)
		}
	}
}

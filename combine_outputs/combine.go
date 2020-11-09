package main

import (
	"bufio"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
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

func main() {

	PATHS := map[string]map[string]string{
		"local": {
			"projectdatapath": "./",
			"outputpath":      ".",
			"climate-data":    "./climate-data/corrected/", // path to climate data
			"ascii-out":       "asciigrids_debug/",         // path to ascii grids
		},
		"Cluster": {
			"projectdatapath": "/project/",
			"outputpath":      "/out/",
			"climate-data":    "/climate-data/", // path to climate data
			"ascii-out":       "asciigrid/",     // path to ascii grids
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

	p := newProcessedData()

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
									} else {
										p.wetHarvestGrid[simKey][idxSource][refIDIndex] = -1
									}
								} else {
									p.coolWeatherImpactGrid[simKey][idxSource][refIDIndex] = -100
									p.coolWeatherDeathGrid[simKey][idxSource][refIDIndex] = -10000
									p.coolWeatherImpactWeightGrid[simKey][idxSource][refIDIndex] = -1
									p.wetHarvestGrid[simKey][idxSource][refIDIndex] = -1
								}
							}
						}
					}
				}

			}(idxSource, sourcefileInfo.Name(), outChan)
		}
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
	for currRuns > 0 {
		select {
		case <-outChan:
			currRuns--
		}
	}
	// part 2: merge To get one past and one future

	// part 2.1 merge all future Climate scenarios per model
	// part 2.2 merge all future climate scenarios over all merged models
	// part 2.3 merge historical over models

	// part 3: generate ascii grids
	waitForNum := 0
	outC := make(chan string)

	// TODO:
	// map of max yield average(30y) over all models and maturity groups
	// map of max yield average(30y) over all models and maturity groups with acceptable variation
	// map max yield maturity groups over all models
	// map max yield maturity groups over all models with acceptable variation

	// The same for the future

	for waitForNum > 0 {
		select {
		case progessStatus := <-outC:
			waitForNum--
			fmt.Println(progessStatus)
		}
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
	outputGridsGenerated        bool
	mux                         sync.Mutex
}

func newProcessedData() (p ProcessedData) {
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
	return p
}
func (p *ProcessedData) mergeFuture() {

	futureScenarioKey := "fut"
	isFuture := func(simKey SimKeyTuple) bool {
		return simKey.climateSenario != "0_0"
	}
	futureKeys := make(map[TreatmentKeyTuple][]SimKeyTuple, 12)
	numSource := 0
	maxRefNo := 0
	for simKey, currGrid := range p.allYieldGrids {
		if isFuture(simKey) {
			fKey := TreatmentKeyTuple{comment: simKey.comment,
				treatNo: simKey.treatNo,
				mGroup:  simKey.mGroup}

			if _, ok := futureKeys[fKey]; !ok {
				futureKeys[fKey] = make([]SimKeyTuple, 0, 5)
				numSource = len(currGrid)
				maxRefNo = len(currGrid[0])
			}
			futureKeys[fKey] = append(futureKeys[fKey], simKey)
		}
	}
	for mergeTreatmentKey, simkeys := range futureKeys {

		// make a simKey for sumarized future
		futureSimKey := SimKeyTuple{climateSenario: futureScenarioKey,
			comment: mergeTreatmentKey.comment,
			mGroup:  mergeTreatmentKey.mGroup,
			treatNo: mergeTreatmentKey.treatNo,
		}
		p.allYieldGrids[futureSimKey] = newGridLookup(numSource, maxRefNo, NONEVALUE)
		p.StdDevAvgGrids[futureSimKey] = newGridLookup(numSource, maxRefNo, NONEVALUE)
		p.harvestGrid[futureSimKey] = newGridLookup(numSource, maxRefNo, NONEVALUE)
		p.matIsHavestGrid[futureSimKey] = newGridLookup(numSource, maxRefNo, NONEVALUE)
		p.lateHarvestGrid[futureSimKey] = newGridLookup(numSource, maxRefNo, NONEVALUE)
		p.coolWeatherImpactGrid[futureSimKey] = newGridLookup(numSource, maxRefNo, NONEVALUE)
		p.coolWeatherDeathGrid[futureSimKey] = newGridLookup(numSource, maxRefNo, NONEVALUE)
		p.coolWeatherImpactWeightGrid[futureSimKey] = newGridLookup(numSource, maxRefNo, NONEVALUE)
		p.wetHarvestGrid[futureSimKey] = newGridLookup(numSource, maxRefNo, NONEVALUE)

		for sIdx := 0; sIdx < numSource; sIdx++ {
			for rIdx := 0; rIdx < maxRefNo; rIdx++ {
				numSimKey := len(simkeys)
				for _, simKey := range simkeys {

				}
				// take the median!
				// std error for climate deviation
				p.allYieldGrids[futureSimKey][sIdx][rIdx]
				p.StdDevAvgGrids[futureSimKey][sIdx][rIdx]
				p.harvestGrid[futureSimKey][sIdx][rIdx]
				p.matIsHavestGrid[futureSimKey][sIdx][rIdx]
				p.lateHarvestGrid[futureSimKey][sIdx][rIdx]
				p.coolWeatherImpactGrid[futureSimKey][sIdx][rIdx]
				p.coolWeatherDeathGrid[futureSimKey][sIdx][rIdx]
				p.coolWeatherImpactWeightGrid[futureSimKey][sIdx][rIdx]
				p.wetHarvestGrid[futureSimKey][sIdx][rIdx]
			}
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
			p.allYieldGrids[simKey] = newGridLookup(numSoures, maxRefNo, NONEVALUE)
			p.StdDevAvgGrids[simKey] = newGridLookup(numSoures, maxRefNo, NONEVALUE)
			p.harvestGrid[simKey] = newGridLookup(numSoures, maxRefNo, NONEVALUE)
			p.matIsHavestGrid[simKey] = newGridLookup(numSoures, maxRefNo, NONEVALUE)
			p.lateHarvestGrid[simKey] = newGridLookup(numSoures, maxRefNo, NONEVALUE)
			p.coolWeatherImpactGrid[simKey] = newGridLookup(numSoures, maxRefNo, NONEVALUE)
			p.coolWeatherDeathGrid[simKey] = newGridLookup(numSoures, maxRefNo, NONEVALUE)
			p.coolWeatherImpactWeightGrid[simKey] = newGridLookup(numSoures, maxRefNo, NONEVALUE)
			p.wetHarvestGrid[simKey] = newGridLookup(numSoures, maxRefNo, NONEVALUE)

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
	mGroup  string
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

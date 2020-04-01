package main

import (
	"bufio"
	"fmt"
	"io/ioutil"
	"log"
	"math"
	"os"
	"path"
	"strconv"
	"strings"
)

const asciiOutFilenameAvg = "avg_%s_trno%s.asc"                             // mGroup_treatmentnumber
const asciiOutFilenameDeviAvg = "devi_avg_%s_trno%s.asc"                    // mGroup_treatmentnumber
const asciiOutFilenameMaxYield = "maxyield_trno%s.asc"                      // treatmentnumber
const asciiOutFilenameMaxYieldMat = "maxyield_matgroup_trno%s.asc"          // treatmentnumber
const asciiOutFilenameMaxYieldDevi = "maxyield_Devi_trno%s.asc"             // treatmentnumber
const asciiOutFilenameMaxYieldMatDevi = "maxyield_Devi_matgroup_trno%s.asc" // treatmentnumber
const asciiOutFilenameWaterDiff = "water_Diff_%s.asc"
const asciiOutFilenameWaterDiffMax = "water_Diff_max_yield.asc"
const asciiOutFilenameSowDoy = "doy_sow_%s_trno%s.asc"          // mGroup_treatmentnumber
const asciiOutFilenameEmergeDoy = "doy_emg_%s_trno%s.asc"       // mGroup_treatmentnumber
const asciiOutFilenameAnthesisDoy = "doy_ant_%s_trno%s.asc"     // mGroup_treatmentnumber
const asciiOutFilenameMatDoy = "doy_mat_%s_trno%s.asc"          // mGroup_treatmentnumber
const asciiOutFilenameCoolWeather = "coolweather_%s_trno%s.asc" // mGroup_treatmentnumber

// USER switch for setting
const USER = "local"

// CROPNAME to analyse
const CROPNAME = "soybean"

// NONEVALUE for ascii table
const NONEVALUE = -9999

func main() {

	// path to files
	PATHS := map[string]map[string]string{
		"local": {
			"sim-result-path": "./out/",                      // path to simulation results
			"climate-data":    "./climate-data/transformed/", // path to climate data
			"ascii-out":       "./asciigrids/",               // path to ascii grids
			"png-out":         "./png/",                      // path to png images
			"pdf-out":         "./pdf-out/",                  // path to pdf package
		},
		"test": {
			"sim-result-path": "./out2/",                     // path to simulation results
			"climate-data":    "./climate-data/transformed/", // path to climate data
			"ascii-out":       "./asciigrids2/",              // path to ascii grids
			"png-out":         "./png2/",                     // path to png images
			"pdf-out":         "./pdf-out2/",                 // path to pdf package
		},
		"Cluster": {
			"sim-result-path": "./out/",               // path to simulation results
			"climate-data":    "./asciigrid_cluster/", // path to climate data
			"ascii-out":       "./asciigrid_cluster/", // path to ascii grids
			"png-out":         "./png_cluster/",       // path to png images
			"pdf-out":         "./pdf-out_cluster/",   // path to pdf package
		},
	}

	pathID := USER

	for _, arg := range os.Args[1:] {
		keyValue := strings.SplitN(arg, "=", 1)
		if keyValue[0] == "path" {
			pathID = keyValue[1]
		}
	}

	inputFolder := PATHS[pathID]["sim-result-path"]
	climateFolder := PATHS[pathID]["climate-data"]
	asciiOutFolder := PATHS[pathID]["ascii-out"]
	pngFolder := PATHS[pathID]["png-out"]
	pdfFolder := PATHS[pathID]["pdf-out"]
	errorFile := path.Join(asciiOutFolder, "error.txt")

	filelist, err := ioutil.ReadDir(inputFolder)
	if err != nil {
		log.Fatal(err)
	}

	extRow, extCol, idxFileDic := fileByGrid(filelist, GridCoord{3, 4})

	maxAllAvgYield := 0
	maxSdtDeviation := 0
	numInput := len(idxFileDic)
	currentInput := 0
	allGrids := make(map[SimKeyTuple][][]int)
	StdDevAvgGrids := make(map[SimKeyTuple][][]int)
	matureGrid := make(map[SimKeyTuple][][]int)
	flowerGrid := make(map[SimKeyTuple][][]int)
	climateFilePeriod := make(map[string]int)
	coolWeatherImpactGrid := make(map[SimKeyTuple][][]int)
	outputGridsGenerated := false

	// iterate over all grid cells
	for currRow := 1; currRow < extRow+1; currRow++ {
		for currCol := 1; currCol < extCol+1; currCol++ {
			gridIndex := GridCoord{currRow, currCol}
			if _, ok := idxFileDic[gridIndex]; ok {
				simulations := make(map[SimKeyTuple][]float64)
				simDoyFlower := make(map[SimKeyTuple][]int)
				simDoyMature := make(map[SimKeyTuple][]int)
				dateYearOrder := make(map[SimKeyTuple][]int)
				firstLine := true
				var header SimDataIndex
				// open grid cell file
				sourcefile, err := os.Open(path.Join(inputFolder, idxFileDic[gridIndex]))
				if err != nil {
					log.Fatal(err)
				}
				defer sourcefile.Close()
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
						if IsCrop(lineContent, CROPNAME) && (lineContent[0] == "T1" || lineContent[0] == "T2") {
							lineKey = (lineContent[:-7])
							yieldValue = lineContent[-1]
							period = lineContent[-7]
							yearValue = lineContent[-6]
							sowValue = lineContent[-5]
							emergeValue = lineContent[-4]
							flowerValue = lineContent[-3]
							matureValue = lineContent[-2]
							harvestValue = lineContent[-2]
							climateFilePeriod[lineKey[1]] = period
							simulations[lineKey].append(yieldValue)
							simDoyFlower[lineKey].append(flowerValue)
							if matureValue > 0 {
								simDoyMature[lineKey].append(matureValue)
							} else {
								simDoyMature[lineKey].append(harvestValue)
							}
							dateYearOrder[lineKey].append(yearValue)
						}
					}
				}

				if !outputGridsGenerated {
					outputGridsGenerated = true
					for simKey := range simulations {
						allGrids[simKey] = newGrid(extRow, extCol, NONEVALUE)
						StdDevAvgGrids[simKey] = newGrid(extRow, extCol, NONEVALUE)
						// sowGrid[simKey]     = newGrid(extRow, extCol, NONEVALUE)
						// emergeGrid[simKey] = newGrid(extRow, extCol, NONEVALUE)
						matureGrid[simKey] = newGrid(extRow, extCol, NONEVALUE)
						flowerGrid[simKey] = newGrid(extRow, extCol, NONEVALUE)
						coolWeatherImpactGrid[simKey] = newGrid(extRow, extCol, NONEVALUE)
						coolWeatherDeathGrid[simKey] = newGrid(extRow, extCol, NONEVALUE)
					}
				}
				for simKey := range simulations {
					pixelValue = CalculatePixel(simulations[simKey])
					if pixelValue > maxAllAvgYield {
						maxAllAvgYield = pixelValue
					}
					stdDeviation = statistics.stdev(simulations[simKey])
					if stdDeviation > maxSdtDeviation {
						maxSdtDeviation = stdDeviation
					}
					matureGrid[simKey][currRow-1][currCol-1] = int(average(simDoyMature[simKey]))
					flowerGrid[simKey][currRow-1][currCol-1] = int(average(simDoyFlower[simKey]))

					allGrids[simKey][currRow-1][currCol-1] = int(pixelValue)
					StdDevAvgGrids[simKey][currRow-1][currCol-1] = int(stdDeviation)
				}
				//coolWeatherImpactGrid
				for scenario := range climateFilePeriod {
					climatePath = path.Join(climateFolder, climateFilePeriod[scenario], scenario, fmt.Sprintf("%d_%03d_v2.csv", currRow, currCol))
					if _, err := os.Stat(climatePath); err == nil {
						climatefile, err := os.Open(climatePath)
						if err != nil {
							log.Fatal(err)
						}
						defer climatefile.Close()
						firstLines := 0
						numOccurenceHigh := make(map[SimKeyTuple]int)
						numOccurenceMedium := make(map[SimKeyTuple]int)
						numOccurenceLow := make(map[SimKeyTuple]int)
						minValue := 10.0
						var header ClimateHeader
						scanner := bufio.NewScanner(climatefile)
						for scanner.Scan() {
							line := scanner.Text()
							if firstLines < 2 {
								// read header
								if firstLines < 1 {
									header = readClimateHeader(line)
								}
								firstLines++
							} else {
								// load relevant line content
								lineContent = loadClimateLine(line, header)
								date = lineContent[0]
								tmin = lineContent[1]
								dateYear = GetYear(date)
								if tmin < 15 {
									for simKey := range dateYearOrder {
										if simKey[1] == scenario {
											yearIndex = dateYearOrder[simKey].Find(dateYear)
											if yearIndex == -1 {
												break
											}
											startDOY = simDoyFlower[simKey][yearIndex]
											endDOY = simDoyMature[simKey][yearIndex]
											if IsDateInGrowSeason(startDOY, endDOY, date) {
												if _, ok := numOccurenceHigh[simKey]; !ok {
													numOccurenceHigh[simKey] = 0
													numOccurenceMedium[simKey] = 0
													numOccurenceLow[simKey] = 0
												}
												if tmin < 8 {
													numOccurenceHigh[simKey]++
												} else if tmin < 10 {
													numOccurenceMedium[simKey]++
												} else {
													numOccurenceLow[simKey]++
												}
											}
										}
									}
								}
							}
						}
						for simKey := range simulations {
							if allGrids[simKey][currRow-1][currCol-1] > 0 {
								if _, ok := numOccurenceMedium[simKey]; ok {
									sumOccurence = numOccurenceMedium[simKey] + numOccurenceHigh[simKey] + numOccurenceLow[simKey]
									sumDeathOccurence = numOccurenceMedium[simKey]*10 + numOccurenceHigh[simKey]*100 + numOccurenceLow[simKey]
									coolWeatherImpactGrid[simKey][currRow-1][currCol-1] = sumOccurence
									coolWeatherDeathGrid[simKey][currRow-1][currCol-1] = sumDeathOccurence
									if sumMaxOccurence < sumOccurence {
										sumMaxOccurence = sumOccurence
									}
									if sumMaxDeathOccurence < sumDeathOccurence {
										sumMaxDeathOccurence = sumDeathOccurence
									}
								} else {
									coolWeatherImpactGrid[simKey][currRow-1][currCol-1] = 0
									coolWeatherDeathGrid[simKey][currRow-1][currCol-1] = 0
								}
							} else {
								coolWeatherImpactGrid[simKey][currRow-1][currCol-1] = -100
								coolWeatherDeathGrid[simKey][currRow-1][currCol-1] = -100
							}
						}
					}
				}
				currentInput++
				progress(currentInput, numInput, str(currentInput)+" of "+str(numInput))

			} else {
				continue
			}
		}

	}
}

// SimKeyTuple key to identify each simulatio setup
type SimKeyTuple struct {
	treatNo        string
	climateSenario string
	mGroup         string
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

func readHeader(line string) (indices SimDataIndex) {
	//read header
	tokens = strings.Split(line, ",")
	indices{
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
	i := -1
	for _, token := range tokens {
		i = i + 1
		switch token {
		case "Crop":
			indices.mGroupCIdx = i
		case "sce":
			indices.climateSenarioCIdx = i
		case "Yield":
			indices.yieldsCIdx = i
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

func fileByGrid(filelist []os.FileInfo, tokenPositions GridCoord) (extRow int, extCol int, idxFileDic map[GridCoord]string) {
	idxFileDic = make(map[GridCoord]string)
	for _, file := range filelist {
		filename := file.Name()
		grid := GetGridfromFilename(filename, tokenPositions)
		if grid.row == -1 {
			continue
		} else {
			if extRow < grid.row {
				extRow = grid.row
			}
			if extCol < grid.col {
				extCol = grid.col
			}
		}
		//indexed file list by grid, remove all none csv
		idxFileDic[grid] = filename
	}
	return extRow, extCol, idxFileDic
}

// GetGridfromFilename get GridCoord from filename
func GetGridfromFilename(filename string, tokenPositions GridCoord) GridCoord {
	basename := path.Base(filename)
	rolColTuple := GridCoord{-1, -1}
	if strings.HasSuffix(basename, ".csv") {
		basename = basename[:len(basename)-4]
		tokens := strings.Split(basename, "_")
		row, err := strconv.ParseInt(tokens[tokenPositions.row], 10, 64)
		if err != nil {
			log.Fatal(err)
		}
		col, err := strconv.ParseInt(tokens[tokenPositions.col], 10, 64)
		if err != nil {
			log.Fatal(err)
		}
		rolColTuple = GridCoord{int(row), int(col)}
	}
	return rolColTuple
}

func makeDir(outPath string) {
	if _, err := os.Stat(outPath); os.IsNotExist(err) {
		if err := os.MkdirAll(outPath, os.ModePerm); err != nil {
			log.Fatalf("ERROR: Failed to generate output path %s :%v", outPath, err)
		}
	}
}

func progress(count int, total int, status string) {
	barLen := 60
	filledLen := int(math.Round(float64(barLen*count) / float64(total)))

	percents := math.Round((float64(100*count)/float64(total))*10.0) / 10.0
	bar := '='*filledLen + '-'*(barLen-filledLen)

	fmt.Printf("[%s] %s%s ...%s\r", bar, percents, '%', status)
}

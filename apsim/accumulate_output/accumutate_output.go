package main

import (
	"bufio"
	"encoding/csv"
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

const na = "na"

func main() {

	inputFolderPtr := flag.String("in", "/beegfs/rpm/projects/apsim/projects/soybeanEU/out_0_0_0", "path to input")
	outFolderPtr := flag.String("out", "/beegfs/rpm/projects/apsim/projects/soybeanEU/out_transformed", "path to output")
	// inputFolderPtr := flag.String("in", "C:/Users/sschulz/Desktop/out_0_0_0", "path to input")
	// outFolderPtr := flag.String("out", "C:/Users/sschulz/Desktop/out_0_0_0_transformed", "path to output")
	baseCSVPtr := flag.String("base", "./base.csv", "base csv file")
	periodPtr := flag.String("period", "0", "periode")
	scePtr := flag.String("sce", "0_0", "climate scenatrio")
	CO2Ptr := flag.String("co2", "360", "co2 value")
	concurrentPtr := flag.Int("concurrent", 40, "concurrent generation")

	flag.Parse()

	inputFolder := *inputFolderPtr
	outFolder := *outFolderPtr
	baseCSV := *baseCSVPtr
	period := *periodPtr
	sce := *scePtr
	CO2 := *CO2Ptr
	numConcurrent := *concurrentPtr

	baseFile, err := os.Open(baseCSV)
	if err != nil {
		log.Fatal(err)
	}
	defer baseFile.Close()

	baseReader := csv.NewReader(baseFile)
	//"","soil_ref","CLocation","latitude","soil","irrigation","MG","metfiles","fert_criteria","template","sample.xml","initialwater.xml","id","nr","OUT","start_date","end_date","Commander"
	var headerIndex map[string]int

	baseData := make([]baseSet, 198734)
	baseDataLookup := make(map[int64][]int, 99367)

	index := -1
	for {
		record, err := baseReader.Read()

		if err == io.EOF {
			break
		}
		if err != nil {
			log.Fatal(err)
		}
		if index < 0 {
			headerIndex = make(map[string]int, len(record))
			for i, header := range record {
				if i > 0 {
					headerIndex[strings.Trim(header, "\"")] = i
				}
			}
			index++
			continue
		}
		soilRef, err := strconv.ParseInt(record[headerIndex["soil_ref"]], 10, 32)
		if err != nil {
			log.Fatal(err)
		}
		noIrrigation := strings.HasPrefix(record[headerIndex["irrigation"]], "no_")
		id := record[headerIndex["nr"]]
		baseData[index] = baseSet{soilRef, !noIrrigation, id}
		if _, ok := baseDataLookup[soilRef]; !ok {
			baseDataLookup[soilRef] = make([]int, 2)
			baseDataLookup[soilRef][0] = index
		} else {
			baseDataLookup[soilRef][1] = index
		}
		index++
	}

	folderMapping := getFolderMaturityGroupMapping(inputFolder)

	out := make(chan string)
	current := 0
	for soilRef, soilRefVal := range baseDataLookup {

		for current >= numConcurrent {
			select {
			case isOK, isOpen := <-out:
				if !isOpen {
					log.Fatal("output channel unexpected close")
				}
				log.Println(isOK)
				current--
				break
			}
		}
		current++
		go doFile(soilRef, soilRefVal, &baseData, &folderMapping, outFolder, period, CO2, sce, out)
	}
	for current > 0 {
		select {
		case isOK, isOpen := <-out:
			if !isOpen {
				log.Fatal("output channel unexpected close")
			}
			log.Println(isOK)
			current--
			if current == 0 {
				return
			}
		}
	}

}

func doFile(soilRef int64, soilRefVal []int, baseData *[]baseSet, folderMapping *map[string]string, outFolder, period, CO2, sce string, out chan string) {
	soilRefStr := strconv.Itoa(int(soilRef))
	fulloutpath := filepath.Join(outFolder, "EU_SOY_AP_"+soilRefStr+".csv")
	makeDir(fulloutpath)
	fmt.Println(fulloutpath)
	exists := true
	if _, err := os.Stat(fulloutpath); err != nil {
		exists = false
	}

	outFile, err := os.OpenFile(fulloutpath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		log.Fatal(err)
	}
	writer := bufio.NewWriter(outFile)
	if !exists {
		writer.WriteString(outputHeader)
	}

	for _, irrSetup := range soilRefVal {
		id := (*baseData)[irrSetup].id
		for matGroupCRot, folder := range *folderMapping {
			var firstCrop string
			var prefix string
			var matGroup string
			if strings.HasSuffix(matGroupCRot, "_ms") {
				firstCrop = "maize"
				matGroup = strings.TrimSuffix(matGroupCRot, "_ms")
				prefix = filepath.Join(folder, id+matGroup+"_ms ")
			} else {
				matGroup = strings.TrimSuffix(matGroupCRot, "_sm")
				firstCrop = "soybean"
				prefix = filepath.Join(folder, id+matGroup+"_sm ")
			}

			headerSow, contentSow := readApsimFile(prefix + "sowing.out")
			// SowDOY     AWC_30_sow     AWC_60_sow     AWC_90_sow           year
			findIndex := func(name string, arr []string) int {
				for i, val := range arr {
					if val == name {
						return i
					}
				}
				return -1
			}
			indexSow := findIndex("SowDOY", headerSow)
			indexAWC30sow := findIndex("AWC_30_sow", headerSow)
			indexAWC60sow := findIndex("AWC_60_sow", headerSow)
			indexAWC90sow := findIndex("AWC_90_sow", headerSow)
			indexYear := findIndex("year", headerSow)
			// if SowDOY > 250 ignore line- > bug in Apsim
			type content struct {
				year        string
				SowDOY      string
				AWC30sow    string
				AWC60sow    string
				AWC90sow    string
				EmergDOY    string
				AntDOY      string
				MatDOY      string
				HarvDOY     string
				CO2         string
				Yield       string
				MaxLAI      string
				cyclelength string
				sumET       string
				AWC3014Mar  string
				AWC6014Mar  string
				AWC9014Mar  string
				AWC30harv   string
				AWC60harv   string
				AWC90harv   string
				frostred    string
				sumirri     string
				sumNmin     string
				Crop        string
			}
			datesMapping := make(map[string]*content, 30)
			for _, line := range contentSow {
				sowVal, err := strconv.ParseInt(line[indexSow], 10, 64)
				if err != nil {
					log.Fatal(err)
				}
				if sowVal <= 250 {
					c := content{
						year:        line[indexYear],
						SowDOY:      line[indexSow],
						AWC30sow:    line[indexAWC30sow],
						AWC60sow:    line[indexAWC60sow],
						AWC90sow:    line[indexAWC90sow],
						EmergDOY:    na,
						AntDOY:      na,
						MatDOY:      na,
						HarvDOY:     na,
						Yield:       na,
						MaxLAI:      na,
						cyclelength: na,
						sumET:       na,
						AWC3014Mar:  na,
						AWC6014Mar:  na,
						AWC9014Mar:  na,
						AWC30harv:   na,
						AWC60harv:   na,
						AWC90harv:   na,
						frostred:    na,
						sumirri:     na,
						sumNmin:     na,
						Crop:        "maize/silage maize",
					}
					datesMapping[line[indexYear]] = &c
				}
			}
			headerEmerg, contentEmerg := readApsimFile(prefix + "emerg.out")
			// EmergDOY           year
			indexEmerg := findIndex("EmergDOY", headerEmerg)
			indexYear = findIndex("year", headerEmerg)
			for _, line := range contentEmerg {
				if _, ok := datesMapping[line[indexYear]]; ok {
					str := line[indexEmerg]
					datesMapping[line[indexYear]].EmergDOY = str
				}
			}
			// title         AntDOY           year
			headerAnt, contentAnt := readApsimFile(prefix + "flowering.out")
			indexAnt := findIndex("AntDOY", headerAnt)
			indexYear = findIndex("year", headerAnt)
			for _, line := range contentAnt {
				if _, ok := datesMapping[line[indexYear]]; ok {
					str := line[indexAnt]
					datesMapping[line[indexYear]].AntDOY = str
				}
			}
			//            year         MatDOY              title
			headerMat, contentMat := readApsimFile(prefix + "maturity.out")
			indexMat := findIndex("MatDOY", headerMat)
			indexYear = findIndex("year", headerMat)
			for _, line := range contentMat {
				if _, ok := datesMapping[line[indexYear]]; ok {
					str := line[indexMat]
					datesMapping[line[indexYear]].MatDOY = str
				}
			}
			//       model       year       CO2      maize_lai  soybean_lai  maize_biomass soybean_biomass    maize_yield  soybean_yield
			//       HarvDOY     sum_irri   sum_ep   sum_es     sum_runoff   sum_Nmin paddock.soybean.grain_n paddock.maize.grain_n
			//       AWC_30_harv    AWC_60_harv    AWC_90_harv              title
			headerHar, contentHar := readApsimFile(prefix + "harvesting.out")
			indexYear = findIndex("year", headerHar)
			indexMaizelai := findIndex("maize_lai", headerHar)
			indexSoybeanlai := findIndex("soybean_lai", headerHar)
			indexMaizebiomass := findIndex("maize_biomass", headerHar)
			indexSoybeanbiomass := findIndex("soybean_biomass", headerHar)
			indexMaizeyield := findIndex("maize_yield", headerHar)
			indexSoybeanyield := findIndex("soybean_yield", headerHar)
			indexHarvDOY := findIndex("HarvDOY", headerHar)
			indexSumirri := findIndex("sum_irri", headerHar)
			indexSumep := findIndex("sum_ep", headerHar)
			indexSumes := findIndex("sum_es", headerHar)
			indexSumNmin := findIndex("sum_Nmin", headerHar)
			indexAWC30harv := findIndex("AWC_30_harv", headerHar)
			indexAWC60harv := findIndex("AWC_60_harv", headerHar)
			indexAWC90harv := findIndex("AWC_90_harv", headerHar)

			expectedCrop := "soybean"
			if firstCrop == "soybean" {
				expectedCrop = "maize"
			}
			currentYear := ""
			for _, line := range contentHar {
				year := line[indexYear]
				if currentYear != year {
					if expectedCrop == "maize" {
						expectedCrop = "soybean"
					} else {
						expectedCrop = "maize"
					}
					currentYear = year
				}
				if _, ok := datesMapping[year]; ok {
					str := line[indexHarvDOY]
					if datesMapping[year].HarvDOY == na {
						datesMapping[year].HarvDOY = str
					} else {
						harVal, err := strconv.ParseInt(str, 10, 64)
						if err != nil {
							log.Fatal(err)
						}
						lastHarVal, err := strconv.ParseInt(datesMapping[year].HarvDOY, 10, 64)
						if harVal < lastHarVal {
							datesMapping[year].HarvDOY = str
						}
					}

					soybeanBiomass, err := strconv.ParseFloat(line[indexSoybeanbiomass], 64)
					if err != nil {
						log.Fatal(err)
					}
					maizeBiomass, err := strconv.ParseFloat(line[indexMaizebiomass], 64)
					if err != nil {
						log.Fatal(err)
					}

					yield := line[indexSoybeanyield]
					maxLAI := line[indexSoybeanlai]
					biomass := soybeanBiomass
					if soybeanBiomass < maizeBiomass {
						yield = line[indexMaizeyield]
						maxLAI = line[indexMaizelai]
						biomass = maizeBiomass
					}
					datesMapping[year].Yield = yield
					datesMapping[year].MaxLAI = maxLAI

					if soybeanBiomass > maizeBiomass {
						datesMapping[year].Crop = matGroupMapping[matGroup]
						if expectedCrop != "soybean" {
							log.Fatal("mixed up crop rotation")
						}
					} else if maizeBiomass > soybeanBiomass && expectedCrop != "maize" {
						if expectedCrop != "maize" {
							log.Fatal("mixed up crop rotation")
						}
					} else if soybeanBiomass == maizeBiomass {
						if expectedCrop == "soybean" {
							datesMapping[year].Crop = matGroupMapping[matGroup]
						}
					}
					sumes, err := strconv.ParseFloat(line[indexSumes], 64)
					if err != nil {
						log.Fatal(err)
					}
					sumep, err := strconv.ParseFloat(line[indexSumep], 64)
					if err != nil {
						log.Fatal(err)
					}
					sumET := sumes + sumep
					datesMapping[year].sumET = fmt.Sprintf("%.1f", sumET)

					if biomass > 0 {
						datesMapping[year].AWC30harv = line[indexAWC30harv]
						datesMapping[year].AWC60harv = line[indexAWC60harv]
						datesMapping[year].AWC90harv = line[indexAWC90harv]
					}
					datesMapping[year].sumirri = line[indexSumirri]
					datesMapping[year].sumNmin = line[indexSumNmin]
				}

			}

			for _, datemap := range datesMapping {

				writer.WriteString("AP,")      // write model name shortcut
				writer.WriteString(soilRefStr) // soil_ref
				writer.WriteRune(',')
				// first_crop
				writer.WriteString(firstCrop)
				writer.WriteRune(',')
				// Crop
				writer.WriteString(datemap.Crop)
				writer.WriteRune(',')
				// period
				writer.WriteString(period)
				writer.WriteRune(',')
				// sce
				writer.WriteString(sce)
				writer.WriteRune(',')
				// CO2
				writer.WriteString(CO2)
				writer.WriteRune(',')
				// TrtNo
				writer.WriteString(trtNoMapping[(*baseData)[irrSetup].irrigation])
				writer.WriteRune(',')
				// ProductionCase
				writer.WriteString(productionCaseMapping[(*baseData)[irrSetup].irrigation])
				writer.WriteRune(',')
				// Year
				writer.WriteString(datemap.year)
				writer.WriteRune(',')
				// Yield
				writer.WriteString(datemap.Yield)
				writer.WriteRune(',')
				// MaxLAI
				writer.WriteString(datemap.MaxLAI)
				writer.WriteRune(',')
				// SowDOY
				writer.WriteString(datemap.SowDOY)
				writer.WriteRune(',')
				// EmergDOY
				writer.WriteString(datemap.EmergDOY)
				writer.WriteRune(',')
				// AntDOY
				writer.WriteString(datemap.AntDOY)
				writer.WriteRune(',')
				// MatDOY
				writer.WriteString(datemap.MatDOY)
				writer.WriteRune(',')
				// HarvDOY
				writer.WriteString(datemap.HarvDOY)
				writer.WriteRune(',')
				// sum_ET
				writer.WriteString(datemap.sumET)
				writer.WriteRune(',')
				// AWC_30_sow
				writer.WriteString(datemap.AWC30sow)
				writer.WriteRune(',')
				// AWC_60_sow
				writer.WriteString(datemap.AWC60sow)
				writer.WriteRune(',')
				// AWC_90_sow
				writer.WriteString(datemap.AWC90sow)
				writer.WriteRune(',')
				// AWC_30_harv
				writer.WriteString(datemap.AWC30harv)
				writer.WriteRune(',')
				// AWC_60_harv
				writer.WriteString(datemap.AWC60harv)
				writer.WriteRune(',')
				// AWC_90_harv
				writer.WriteString(datemap.AWC90harv)
				writer.WriteRune(',')
				// tradef
				writer.WriteString(na)
				writer.WriteRune(',')
				// sum_irri
				writer.WriteString(datemap.sumirri)
				writer.WriteRune(',')
				// sum_Nmin
				writer.WriteString(datemap.sumNmin)
				writer.WriteRune(',')
				writer.WriteString("\r\n")
			}
		}
	}
	writer.Flush()
	outFile.Close()
	out <- soilRefStr
}

var outputHeader = "Model,soil_ref,first_crop,Crop,period,sce,CO2,TrtNo,ProductionCase,Year,Yield,MaxLAI,SowDOY,EmergDOY,AntDOY,MatDOY,HarvDOY,sum_ET,AWC_30_sow,AWC_60_sow,AWC_90_sow,AWC_30_harv,AWC_60_harv,AWC_90_harv,tradef,sum_irri,sum_Nmin\r\n"

func getFolderMaturityGroupMapping(inputFolder string) map[string]string {

	out := make(map[string]string, 6)

	// list subfolder for maturity groups
	// create a mapping of folder and maturity group
	// <00078942><Augusta>_<ms> <harvesting>.out
	// 9 digit matGroup crop_rotation stage
	iDir, err := os.Open(inputFolder)
	if err != nil {
		log.Fatal(err)
	}
	defer iDir.Close()

	subFolderNames, err := iDir.Readdir(-1)

	for _, subfolder := range subFolderNames {
		if subfolder.IsDir() {
			subDirfile, err := os.Open(filepath.Join(inputFolder, subfolder.Name()))
			if err != nil {
				log.Fatal(err)
			}
			defer subDirfile.Close()
			filenames, err := subDirfile.Readdir(1)
			for _, filename := range filenames {
				name := filename.Name()
				filenameparts := strings.FieldsFunc(name[8:], func(r rune) bool {
					if r == ' ' {
						return true
					}
					return false
				})
				maturityGroupCR := filenameparts[0]
				out[maturityGroupCR] = filepath.Join(inputFolder, subfolder.Name())
			}
		}
	}
	return out
}

func readApsimFile(filename string) (header []string, content [][]string) {
	file, err := os.Open(filename)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()
	content = make([][]string, 0, 60)
	scanner := bufio.NewScanner(file)
	index := 0
	for scanner.Scan() {
		index++
		if index < 3 || index == 4 {
			continue
		}
		if index == 3 {
			header = strings.Fields(scanner.Text())
			continue
		}

		content = append(content, strings.Fields(scanner.Text()))
	}
	return header, content
}

func makeDir(outPath string) {
	dir := filepath.Dir(outPath)
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		if err := os.MkdirAll(dir, os.ModePerm); err != nil {
			log.Fatalf("ERROR: Failed to generate output path %s :%v", dir, err)
		}
	}
}

type baseSet struct {
	soilRef    int64
	irrigation bool
	id         string
}

var productionCaseMapping = map[bool]string{
	true:  "Unlimited water",
	false: "Actual",
}
var trtNoMapping = map[bool]string{
	true:  "T2",
	false: "T1",
}

var matGroupMapping = map[string]string{
	"Augusta": "soybean/0000",
	"Sultana": "soybean/000",
	"Merkur":  "soybean/00",
	"Galina":  "soybean/0",
	"Balkan":  "soybean/I",
	"Ecudor":  "soybean/II",
	"MG_3":    "soybean/III",
}

package main

import (
	"bufio"
	"errors"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
)

//const soilRefNumber = 99367
const soilRefNumber = 10000

//const minlineCount = 2880

var outputHeader = "Model,soil_ref,first_crop,Crop,period,sce,CO2,TrtNo,ProductionCase,Year,Yield,MaxLAI,SowDOY,EmergDOY,AntDOY,MatDOY,HarvDOY,sum_ET,AWC_30_sow,AWC_60_sow,AWC_90_sow,AWC_30_harv,AWC_60_harv,AWC_90_harv,tradef,sum_irri,sum_Nmin\r\n"

func main() {

	sourcePtr := flag.String("source", "./testout/stics", "path to source folder")
	overridePtr := flag.String("override", "", "path to override source folder")
	outFolderPtr := flag.String("output", "./testout/merged", "path to output folder")
	checkoutputPtr := flag.Bool("checkoutput", false, "check for missing output lines")

	flag.Parse()

	sourceFolder := *sourcePtr
	overrideFolder := *overridePtr
	outFolder := *outFolderPtr
	checkoutput := *checkoutputPtr
	numSources := 0
	if len(sourceFolder) > 0 {
		numSources++
	}
	if len(overrideFolder) > 0 {
		numSources++
	}

	filepathes := make(map[int][]string, soilRefNumber)

	findMatchingFiles := func(inputpath string, pathes map[int][]string) error {
		if len(inputpath) > 0 {
			err := filepath.Walk(inputpath, func(path string, info os.FileInfo, err error) error {
				if err != nil {
					fmt.Printf("prevent panic by handling failure accessing a path %q: %v\n", path, err)
					return err
				}
				if !info.IsDir() {
					refIDStr := strings.Split(strings.Split(info.Name(), ".")[0], "_")[3]
					refID64, err := strconv.ParseInt(refIDStr, 10, 64)
					if err != nil {
						log.Fatal(err)
					}
					refID := int(refID64)
					if _, ok := pathes[refID]; !ok {
						pathes[refID] = make([]string, 0, numSources)
					}
					pathes[refID] = append(pathes[refID], path)
				}

				return nil
			})
			return err
		}
		return nil
	}
	findMatchingFiles(sourceFolder, filepathes)
	if len(overrideFolder) > 0 {
		findMatchingFiles(overrideFolder, filepathes)
	}
	lookup := generateSimKeys()
	for i := 1; i <= soilRefNumber; i++ {
		clearLookup(lookup)
		if _, ok := filepathes[i]; !ok {
			fmt.Printf("%d\n", i)
			// } else if len(filepathes[i]) < numSources {
			// 	fmt.Printf("%d part\n", i)
		} else {
			for _, filePath := range filepathes[i] {
				file, err := os.Open(filePath)
				if err != nil {
					log.Fatal(err)
				}
				scanner := bufio.NewScanner(file)
				index := 0
				for scanner.Scan() {
					index++
					if index > 1 {
						simKey, tokens, err := readSimKey(scanner.Text())
						if err == nil {
							if _, ok := lookup[simKey]; ok {
								lookup[simKey] = tokens
							} else {
								fmt.Println("error:", simKey)
							}

						}
					}
				}
				file.Close()
			}
			if checkoutput {
				checkForMissingData(i, lookup)
			} else {
				// open out file
				// append each source
				soilRef := strconv.Itoa(i)
				fulloutpath := filepath.Join(outFolder, "EU_SOY_ST_"+soilRef+".csv")
				makeDir(fulloutpath)
				//fmt.Println(fulloutpath)

				outFile, err := os.OpenFile(fulloutpath, os.O_TRUNC|os.O_CREATE|os.O_WRONLY, 0660)
				if err != nil {
					log.Fatal(err)
				}
				writer := bufio.NewWriter(outFile)
				writer.WriteString(outputHeader)
				for _, tokens := range lookup {
					for idx, t := range tokens {
						writer.WriteString(t)
						if idx+1 < len(tokens) {
							writer.WriteRune(',')
						}
					}
					writer.WriteString("\r\n")
				}
				writer.Flush()
				outFile.Close()
			}

		}
	}
}

type SimKey struct {
	//Model;soil_ref;first_crop;Crop;period;sce;CO2;TrNo;ProductionCase;Year
	firstCrop  string
	crop       string
	year       string
	climateScn string
	treatment  string
}

func readSimKey(line string) (SimKey, []string, error) {
	tokens := strings.FieldsFunc(line, func(r rune) bool {
		return (r == ',' || r == ';')
	})
	outTokens := make([]string, len(tokens))
	for idx, t := range tokens {
		outTokens[idx] = strings.Trim(t, "\"")
	}
	if outTokens[2] == "first_crop" {
		// catch headline in between
		return SimKey{}, []string{}, errors.New("headline in between")
	}
	//Model;soil_ref;first_crop;Crop;period;sce;CO2;TrNo;ProductionCase;Year
	// 0     1        2           3    4      5  6    7    8             9
	return SimKey{
		firstCrop:  outTokens[2],
		crop:       outTokens[3],
		year:       outTokens[9],
		climateScn: outTokens[5],
		treatment:  outTokens[7],
	}, outTokens, nil
}

func generateSimKeys() map[SimKey][]string {
	lookup := make(map[SimKey][]string)
	allCrops := []string{
		"maize",
		"soybean/0000",
		"soybean/000",
		"soybean/00",
		"soybean/0",
		"soybean/I",
		"soybean/II",
		"soybean/III",
	}
	firstCrops := []string{
		"maize",
		"soybean"}
	year := make([]string, 30)
	for i := 0; i < 30; i++ {
		year[i] = strconv.FormatInt(int64(1981+i), 10)
	}
	climateScn := []string{
		"GISS-E2-R_45",
		"GFDL-CM3_45",
		"HadGEM2-ES_45",
		"MPI-ESM-MR_45",
		"MIROC5_45",
		"0_0",
	}
	treatment := []string{"T1", "T2"}

	for _, t := range treatment {
		for _, y := range year {
			for _, c := range climateScn {
				for _, f := range firstCrops {
					for _, crop := range allCrops {
						key := SimKey{
							firstCrop:  f,
							crop:       crop,
							year:       y,
							climateScn: c,
							treatment:  t,
						}
						lookup[key] = nil
					}
				}
			}
		}
	}
	return lookup
}

func clearLookup(lookup map[SimKey][]string) {
	for key := range lookup {
		lookup[key] = nil
	}
}

func checkForMissingData(id int, lookup map[SimKey][]string) {

	emptyKeyList := make([]SimKey, 0, len(lookup))
	for key := range lookup {
		if lookup[key] == nil {
			emptyKeyList = append(emptyKeyList, key)
		}
	}
	if len(emptyKeyList) > 0 {
		fmt.Println(id, len(lookup)-len(emptyKeyList))
		if len(lookup) > len(emptyKeyList) {

			//missing crop rotation
			firstCrops := []string{
				"maize",
				"soybean"}
			allOfList("firstCrop", emptyKeyList, firstCrops)

			//missing crop rotation
			climateScn := []string{
				"GISS-E2-R_45",
				"GFDL-CM3_45",
				"HadGEM2-ES_45",
				"MPI-ESM-MR_45",
				"MIROC5_45",
				"0_0",
			}
			allOfList("climateScn", emptyKeyList, climateScn)

			allCrops := []string{
				"maize",
				"soybean/0000",
				"soybean/000",
				"soybean/00",
				"soybean/0",
				"soybean/I",
				"soybean/II",
				"soybean/III",
			}
			allOfList("crop", emptyKeyList, allCrops)
		}
	}

}

func allOfList(varName string, emptyKeyList []SimKey, valRefs []string) map[string]bool {

	all := make(map[string]bool, len(valRefs))
	for _, valRef := range valRefs {
		all[valRef] = true
		for _, key := range emptyKeyList {
			v := reflect.ValueOf(key)
			f := v.FieldByName(varName)
			value := f.String()
			if value != valRef {
				all[valRef] = false
				break
			}
		}
		if all[valRef] {
			fmt.Println(varName, ": all of ", valRef)
		}
	}
	return all
}

func makeDir(outPath string) {
	dir := filepath.Dir(outPath)
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		if err := os.MkdirAll(dir, os.ModePerm); err != nil {
			log.Fatalf("ERROR: Failed to generate output path %s :%v", dir, err)
		}
	}
}

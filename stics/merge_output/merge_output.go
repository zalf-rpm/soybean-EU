package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

const soilRefNumber = 99367
const minlineCount = 2880

var outputHeader = "Model,soil_ref,first_crop,Crop,period,sce,CO2,TrtNo,ProductionCase,Year,Yield,MaxLAI,SowDOY,EmergDOY,AntDOY,MatDOY,HarvDOY,sum_ET,AWC_30_sow,AWC_60_sow,AWC_90_sow,AWC_30_harv,AWC_60_harv,AWC_90_harv,tradef,sum_irri,sum_Nmin\r\n"

func main() {

	sourcePtr := flag.String("source", "./testout/stics", "path to source folder")
	overridePtr := flag.String("override", "./testout_other/stics", "path to override source folder")
	outFolderPtr := flag.String("output", "./testout/merged", "path to output folder")
	countLinesPtr := flag.Bool("countoutput", false, "count missing output lines")

	flag.Parse()

	sourceFolder := *sourcePtr
	overrideFolder := *overridePtr
	outFolder := *outFolderPtr
	countLines := *countLinesPtr
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
	findMatchingFiles(overrideFolder, filepathes)

	for i := 1; i <= soilRefNumber; i++ {
		if _, ok := filepathes[i]; !ok {
			fmt.Printf("%d\n", i)
			// } else if len(filepathes[i]) < numSources {
			// 	fmt.Printf("%d part\n", i)
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

			lookup := make(map[SimKey][]string)

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
						simKey, tokens := readSimKey(scanner.Text())
						lookup[simKey] = tokens
					}
				}
				file.Close()
			}
			if countLines && len(lookup) < minlineCount {
				println(i, len(lookup))
			}
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

type SimKey struct {
	//Model;soil_ref;first_crop;Crop;period;sce;CO2;TrNo;ProductionCase;Year
	firstCrop  string
	crop       string
	year       string
	climateScn string
	treatment  string
}

func readSimKey(line string) (SimKey, []string) {
	tokens := strings.FieldsFunc(line, func(r rune) bool {
		return (r == ',' || r == ';')
	})
	outTokens := make([]string, len(tokens))
	for idx, t := range tokens {
		outTokens[idx] = strings.Trim(t, "\"")
	}
	//Model;soil_ref;first_crop;Crop;period;sce;CO2;TrNo;ProductionCase;Year
	// 0     1        2           3    4      5  6    7    8             9
	return SimKey{
		firstCrop:  outTokens[1],
		crop:       outTokens[3],
		year:       outTokens[9],
		climateScn: outTokens[5],
		treatment:  outTokens[7],
	}, outTokens
}

func makeDir(outPath string) {
	dir := filepath.Dir(outPath)
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		if err := os.MkdirAll(dir, os.ModePerm); err != nil {
			log.Fatalf("ERROR: Failed to generate output path %s :%v", dir, err)
		}
	}
}

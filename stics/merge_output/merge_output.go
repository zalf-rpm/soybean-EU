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

var outputHeader = "Model,soil_ref,first_crop,Crop,period,sce,CO2,TrtNo,ProductionCase,Year,Yield,MaxLAI,SowDOY,EmergDOY,AntDOY,MatDOY,HarvDOY,sum_ET,AWC_30_sow,AWC_60_sow,AWC_90_sow,AWC_30_harv,AWC_60_harv,AWC_90_harv,tradef,sum_irri,sum_Nmin\r\n"

func main() {

	source1Ptr := flag.String("source1", "D:/stics_15_03_2021/out", "path to source folder")
	source2Ptr := flag.String("source2", "D:/stics_15_03_2021/MGIII", "path to source folder")
	outFolderPtr := flag.String("output", "D:/stics_15_03_2021/merged", "path to output folder")

	flag.Parse()

	source1Folder := *source1Ptr
	source2Folder := *source2Ptr
	outFolder := *outFolderPtr
	numSources := 0
	if len(source1Folder) > 0 {
		numSources++
	}
	if len(source2Folder) > 0 {
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
	findMatchingFiles(source1Folder, filepathes)
	findMatchingFiles(source2Folder, filepathes)

	for i := 1; i <= soilRefNumber; i++ {
		if _, ok := filepathes[i]; !ok {
			fmt.Printf("%d\n", i)
		} else if len(filepathes[i]) < numSources {
			fmt.Printf("%d part\n", i)
		} else {
			// open out file
			// append each source
			soilRef := strconv.Itoa(i)
			fulloutpath := filepath.Join(outFolder, "EU_SOY_ST_"+soilRef+".csv")
			makeDir(fulloutpath)
			fmt.Println(fulloutpath)

			outFile, err := os.OpenFile(fulloutpath, os.O_TRUNC|os.O_CREATE|os.O_WRONLY, 0600)
			if err != nil {
				log.Fatal(err)
			}
			writer := bufio.NewWriter(outFile)
			writer.WriteString(outputHeader)

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
						tokens := strings.FieldsFunc(scanner.Text(), func(r rune) bool {
							return (r == ',' || r == ';')
						})
						for idx, t := range tokens {
							writer.WriteString(strings.Trim(t, "\""))
							if idx+1 < len(tokens) {
								writer.WriteRune(',')
							}
						}
						writer.WriteString("\r\n")
					}
				}
				file.Close()
			}
			writer.Flush()
			outFile.Close()
		}
	}
}

func makeDir(outPath string) {
	dir := filepath.Dir(outPath)
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		if err := os.MkdirAll(dir, os.ModePerm); err != nil {
			log.Fatalf("ERROR: Failed to generate output path %s :%v", dir, err)
		}
	}
}

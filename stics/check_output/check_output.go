package main

import (
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"strconv"
	"strings"
)

const soilRefNumber = 99367

func main() {

	sourcePtr := flag.String("source", "D:/stics/out", "path to source folder")
	flag.Parse()
	sourceFolder := *sourcePtr
	filelist, err := ioutil.ReadDir(sourceFolder)
	if err != nil {
		log.Fatal(err)
	}
	existingFiles := make(map[int]bool, soilRefNumber)
	for _, file := range filelist {
		ext := strings.Split(file.Name(), ".")
		if len(ext) != 2 {
			fmt.Printf("error %s, wrong format\n", file.Name())
			continue
		}
		parts := strings.Split(ext[0], "_")
		if len(parts) != 4 {
			fmt.Printf("error %s, wrong format\n", file.Name())
			continue
		}
		refIDStr := parts[3]
		refID64, err := strconv.ParseInt(refIDStr, 10, 64)
		if err != nil {
			fmt.Printf("error %s, %v \n", file.Name(), err)
			continue
		}
		existingFiles[int(refID64)] = true
	}

	for i := 1; i <= soilRefNumber; i++ {
		if _, ok := existingFiles[i]; !ok {
			fmt.Printf("%d\n", i)
		}
	}

}

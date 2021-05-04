package main

import (
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"strconv"
	"strings"
)

const soilRefNumber = 99637

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
		refIDStr := strings.Split(strings.Split(file.Name(), ".")[0], "_")[3]
		refID64, err := strconv.ParseInt(refIDStr, 10, 64)
		if err != nil {
			log.Fatal(err)
		}
		existingFiles[int(refID64)] = true
	}

	for i := 1; i <= soilRefNumber; i++ {
		if _, ok := existingFiles[i]; !ok {
			fmt.Printf("%d\n", i)
		}
	}

}

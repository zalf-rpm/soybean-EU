package main

import (
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"os"

	"gopkg.in/yaml.v2"
)

func main() {

	source1 := flag.String("source1", "", "path to source file")
	source2 := flag.String("source2", "", "path to source file")
	flag.Parse()

	meta1 := readMeta(*source1)
	meta2 := readMeta(*source2)

	fmt.Println(max(meta1.MaxValue, meta2.MaxValue))

}

func max(v1, v2 int) int {
	if v1 > v2 {
		return v1
	}
	return v2
}

type Meta struct {
	Title              string   `yaml:"title"`
	YTitle             float64  `yaml:"yTitle"`
	XTitle             float64  `yaml:"xTitle"`
	RemoveEmptyColumns bool     `yaml:"removeEmptyColumns"`
	Labeltext          string   `yaml:"labeltext"`
	Colormap           string   `yaml:"colormap"`
	Colorlist          []string `yaml:"colorlist"`
	Colorlisttype      string   `yaml:"colorlisttype"`
	Factor             float64  `yaml:"factor"`
	MaxValue           int      `yaml:"maxValue"`
	MinValue           int      `yaml:"minValue"`
	MinColor           string   `yaml:"minColor"`
}

func readMeta(source string) Meta {
	meta1 := Meta{
		Title:              "",
		YTitle:             0,
		XTitle:             0,
		RemoveEmptyColumns: false,
		Labeltext:          "",
		Colormap:           "",
		Colorlist:          []string{},
		Colorlisttype:      "",
		Factor:             0,
		MaxValue:           0,
		MinValue:           0,
		MinColor:           "",
	}

	data1, err := ioutil.ReadFile(source)
	if err != nil {
		os.Exit(1)
	}
	err = yaml.Unmarshal([]byte(data1), &meta1)
	if err != nil {
		log.Fatalf("error: %v", err)
	}
	return meta1
}

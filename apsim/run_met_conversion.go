package main

import (
	"flag"
	"fmt"
)

type args struct {
	folderIn  string
	folderOut string
	project   string
	seperator string
	co2       int
}

func main() {
	sourcePtr := flag.String("source", "", "path to source folder")
	outPtr := flag.String("output", "", "path to out folder")
	projPtr := flag.String("project", "", "path to project data")
	co2Ptr := flag.Int("co2", 499, "co2 value")

	flag.Parse()

	cmdl := args{folderIn: *sourcePtr,
		folderOut: *outPtr,
		project:   *projPtr,
		seperator: ",",
		co2:       *co2Ptr}

	if err := ConvertMonicaToMet(cmdl.folderIn, cmdl.folderOut, cmdl.project, cmdl.seperator, cmdl.co2); err != nil {
		fmt.Print(err)
	}

}

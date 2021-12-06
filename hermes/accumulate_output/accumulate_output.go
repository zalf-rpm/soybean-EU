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

const maxSoilRef = 99367
const headline = "Model,soil_ref,first_crop,Crop,period,sce,CO2,TrtNo,ProductionCase,Year,Yield,MaxLAI,SowDOY,EmergDOY,AntDOY,MatDOY,HarvDOY,sum_ET,AWC_30_sow,AWC_60_sow,AWC_90_sow,AWC_30_harv,AWC_60_harv,AWC_90_harv,tradef,sum_irri,sum_Nmin"

func main() {

	inputFolderPtr := flag.String("in", "..", "path to input")
	outFolderPtr := flag.String("out", "..", "path to output")
	concurrentPtr := flag.Int("concurrent", 10, "concurrent generation")
	climScenGroupPtr := flag.String("climGroup", "45", "climate scenario group (4.5 = 45 or 8.5 = 85)")
	co2Ptr := flag.String("co2", "499", "co2 future")

	flag.Parse()
	inputFolder := *inputFolderPtr
	outFolder := *outFolderPtr
	numConcurrent := *concurrentPtr

	scenarioFolder := [...]string{"0_0_0",
		fmt.Sprintf("2_GFDL-CM3_%s", *climScenGroupPtr),
		fmt.Sprintf("2_GISS-E2-R_%s", *climScenGroupPtr),
		fmt.Sprintf("2_HadGEM2-ES_%s", *climScenGroupPtr),
		fmt.Sprintf("2_MIROC5_%s", *climScenGroupPtr),
		fmt.Sprintf("2_MPI-ESM-MR_%s", *climScenGroupPtr)}
	sce := [...]string{"0_0",
		fmt.Sprintf("GFDL-CM3_%s", *climScenGroupPtr),
		fmt.Sprintf("GISS-E2-R_%s", *climScenGroupPtr),
		fmt.Sprintf("HadGEM2-ES_%s", *climScenGroupPtr),
		fmt.Sprintf("MIROC5_%s", *climScenGroupPtr),
		fmt.Sprintf("MPI-ESM-MR_%s", *climScenGroupPtr)}

	period := [...]string{"0", "2", "2", "2", "2", "2"}
	co2 := [...]string{"360", *co2Ptr, *co2Ptr, *co2Ptr, *co2Ptr, *co2Ptr}

	irrigation := [...]string{"Ir", "noIr"}
	matG := [...]string{"0", "00", "000", "0000", "i", "ii", "iii"}
	cRotation := [...]string{"10001", "10002"}

	folderLookup := make(map[int]string, len(scenarioFolder)*len(irrigation)*len(matG))
	for cIdx, cScenario := range scenarioFolder {
		for irIdx, ir := range irrigation {
			for matIdx, mat := range matG {
				folderLookup[cIdx|irIdx<<4|matIdx<<6] = filepath.Join(inputFolder, cScenario, ir, mat)
			}
		}
	}

	current := 0
	out := make(chan string)
	for sRef := 1; sRef <= maxSoilRef; sRef++ {

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

		go func(soilRef int, outChan chan string) {
			var outfile *Fout
			fnLookup := make(map[int]string, 2)
			for cRotidx, cRot := range cRotation {
				fnLookup[cRotidx] = filepath.Join("RESULT", fmt.Sprintf("C%d%s.csv", soilRef, cRot))
			}
			for cIdx := 0; cIdx < len(scenarioFolder); cIdx++ {
				outline := newOutLineContent(co2[cIdx], period[cIdx], sce[cIdx])
				for irIdx, ir := range irrigation {
					for matIdx, mat := range matG {
						for cRotidx, cRot := range cRotation {
							pathToFileC := filepath.Join(folderLookup[cIdx|irIdx<<4|matIdx<<6], fnLookup[cRotidx])
							// pathToFileY := filepath.Join(pathToHermesOutput, ir, mat, "RESULT", fmt.Sprintf("Y%d%s.RES", soilRef, cRot))
							cfile, err := os.Open(pathToFileC)
							if err != nil {
								break
							}
							if outfile == nil {
								outPath := filepath.Join(outFolder, "acc", *climScenGroupPtr, fmt.Sprintf("EU_SOY_HE_%d.csv", soilRef))
								makeDir(outPath)
								file, err := os.OpenFile(outPath, os.O_TRUNC|os.O_CREATE|os.O_WRONLY, 0600)
								if err != nil {
									log.Fatal(err)
								}
								outfile = &Fout{file, bufio.NewWriter(file)}
								outfile.WriteString(headline)
								outfile.WriteString("\r\n")
							}
							scanner := bufio.NewScanner(cfile)
							lineIdx := -1
							var columIdxC map[header]int
							for scanner.Scan() {
								lineIdx++
								if lineIdx == 0 {
									columIdxC = readHeader(scanner.Text())
								}
								if lineIdx > 0 {
									token := strings.Split(scanner.Text(), ",")
									outline.soilref = strconv.Itoa(soilRef)
									outline.SowDOY = token[columIdxC[sowingDOY]]
									outline.EmergDOY = token[columIdxC[emergDOY]]
									outline.AntDOY = token[columIdxC[anthDOY]]
									outline.MatDOY = token[columIdxC[matDOY]]
									outline.HarvDOY = token[columIdxC[harvestDOY]]
									outline.Year = token[columIdxC[year]]
									outline.Yield = token[columIdxC[yield]]
									outline.MaxLAI = token[columIdxC[laimax]]
									outline.sumirri = token[columIdxC[irrig]]
									outline.sumET = token[columIdxC[eTsum]]
									outline.AWC30harv = token[columIdxC[aWC30harv]]
									outline.AWC30sow = token[columIdxC[aWC30sow]]
									outline.sumNmin = token[columIdxC[sumNmin]]

									outline.TrtNo = trtNoMapping[ir]
									outline.ProductionCase = productionCaseMapping[ir]
									outline.firstcrop = fistCrop[cRot]
									if token[columIdxC[crop]] == "SOY" {
										outline.Crop = matGroupMapping[mat]
									} else {
										outline.Crop = matGroupMapping["maize"]
									}
									outfile.writeOutLineContent(&outline, ',')
								}
							}
							cfile.Close()
						}
					}
				}
			}
			if outfile != nil {
				outfile.Close()
				outfile = nil
			}
			outChan <- fmt.Sprintf("%d ", soilRef)
		}(sRef, out)
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

type header int

const (
	sowingDOY header = iota
	emergDOY
	anthDOY
	matDOY
	harvestDOY
	year
	crop
	yield
	laimax
	irrig
	eTsum
	aWC30sow
	aWC30harv
	sumNmin
)

func readHeader(line string) map[header]int {
	//read header
	tokens := strings.Split(line, ",")
	indices := map[header]int{
		sowingDOY:  -1,
		emergDOY:   -1,
		anthDOY:    -1,
		matDOY:     -1,
		harvestDOY: -1,
		year:       -1,
		crop:       -1,
		yield:      -1,
		laimax:     -1,
		irrig:      -1,
		eTsum:      -1,
		aWC30sow:   -1,
		aWC30harv:  -1,
		sumNmin:    -1,
	}

	for i, token := range tokens {
		switch token {
		case "Crop":
			indices[crop] = i
		case "Yield":
			indices[yield] = i
		case "EmergDOY":
			indices[emergDOY] = i
		case "SowDOY":
			indices[sowingDOY] = i
		case "AntDOY":
			indices[anthDOY] = i
		case "MatDOY":
			indices[matDOY] = i
		case "HarvDOY":
			indices[harvestDOY] = i
		case "Year":
			indices[year] = i
		case "MaxLAI":
			indices[laimax] = i
		case "sum_ET":
			indices[eTsum] = i
		case "sum_irri":
			indices[irrig] = i
		case "AWC_30_sow":
			indices[aWC30sow] = i
		case "AWC_30_harv":
			indices[aWC30harv] = i
		case "sum_Nmin":
			indices[sumNmin] = i
		}
	}

	return indices
}

type outLineContent struct {
	Model          string
	soilref        string
	firstcrop      string
	Crop           string
	period         string
	sce            string
	CO2            string
	TrtNo          string
	ProductionCase string
	Year           string
	Yield          string
	MaxLAI         string
	SowDOY         string
	EmergDOY       string
	AntDOY         string
	MatDOY         string
	HarvDOY        string
	sumET          string
	AWC30sow       string
	AWC60sow       string
	AWC90sow       string
	AWC30harv      string
	AWC60harv      string
	AWC90harv      string
	tradef         string
	sumirri        string
	sumNmin        string
}

func newOutLineContent(co2, period, sce string) outLineContent {
	return outLineContent{
		Model:          "HE",
		soilref:        "n.a",
		firstcrop:      "n.a",
		Crop:           "n.a",
		period:         period,
		sce:            sce,
		CO2:            co2,
		TrtNo:          "n.a",
		ProductionCase: "n.a",
		Year:           "n.a",
		Yield:          "n.a",
		MaxLAI:         "n.a",
		SowDOY:         "n.a",
		EmergDOY:       "n.a",
		AntDOY:         "n.a",
		MatDOY:         "n.a",
		HarvDOY:        "n.a",
		sumET:          "n.a",
		AWC30sow:       "n.a",
		AWC60sow:       "n.a",
		AWC90sow:       "n.a",
		AWC30harv:      "n.a",
		AWC60harv:      "n.a",
		AWC90harv:      "n.a",
		tradef:         "n.a",
		sumirri:        "n.a",
		sumNmin:        "n.a",
	}
}

var productionCaseMapping = map[string]string{
	"Ir":   "Unlimited water",
	"noIr": "Actual",
}
var trtNoMapping = map[string]string{
	"Ir":   "T2",
	"noIr": "T1",
}
var matGroupMapping = map[string]string{
	"0000":  "soybean/0000",
	"000":   "soybean/000",
	"00":    "soybean/00",
	"0":     "soybean/0",
	"i":     "soybean/I",
	"ii":    "soybean/II",
	"iii":   "soybean/III",
	"maize": "maize/silage maize",
}
var fistCrop = map[string]string{
	"10001": "soybean",
	"10002": "maize",
}

// Fout file output struct
type Fout struct {
	file    *os.File
	fwriter *bufio.Writer
}

// WriteString string to bufferd file
func (f *Fout) WriteString(s string) (int, error) {
	return f.fwriter.WriteString(s)
}

// Write writes a bufferd byte array
func (f *Fout) Write(s []byte) (int, error) {
	return f.fwriter.Write(s)
}

// WriteRune writes a bufferd rune
func (f *Fout) WriteRune(s rune) (int, error) {
	return f.fwriter.WriteRune(s)
}

func (f *Fout) writeOutLineContent(s *outLineContent, seperator rune) (int, error) {
	var numAll int
	var overAll error

	doWrite := func(olc string, writeSeperator bool) {
		num, err := f.fwriter.WriteString(olc)
		numAll = numAll + num
		if err != nil {
			overAll = err
		}
		if writeSeperator {
			num, err := f.fwriter.WriteRune(seperator)
			if err != nil {
				overAll = err
			}
			numAll = numAll + num
		}
	}
	doWrite(s.Model, true)
	doWrite(s.soilref, true)
	doWrite(s.firstcrop, true)
	doWrite(s.Crop, true)
	doWrite(s.period, true)
	doWrite(s.sce, true)
	doWrite(s.CO2, true)
	doWrite(s.TrtNo, true)
	doWrite(s.ProductionCase, true)
	doWrite(s.Year, true)
	doWrite(s.Yield, true)
	doWrite(s.MaxLAI, true)
	doWrite(s.SowDOY, true)
	doWrite(s.EmergDOY, true)
	doWrite(s.AntDOY, true)
	doWrite(s.MatDOY, true)
	doWrite(s.HarvDOY, true)
	doWrite(s.sumET, true)
	doWrite(s.AWC30sow, true)
	doWrite(s.AWC60sow, true)
	doWrite(s.AWC90sow, true)
	doWrite(s.AWC30harv, true)
	doWrite(s.AWC60harv, true)
	doWrite(s.AWC90harv, true)
	doWrite(s.tradef, true)
	doWrite(s.sumirri, true)
	doWrite(s.sumNmin, false)
	num, err := f.fwriter.WriteString("\r\n")
	numAll = numAll + num
	if err != nil {
		overAll = err
	}
	return numAll, overAll
}

// Close file writer
func (f *Fout) Close() {
	err := f.fwriter.Flush()
	if err != nil {
		log.Fatalln(err)
	}
	err = f.file.Close()
	if err != nil {
		log.Fatalln(err)
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

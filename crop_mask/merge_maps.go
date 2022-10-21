package main

import (
	"bufio"
	"compress/gzip"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

const NONEVALUE = -9999
const projectpath = "C:/Users/sschulz/go/src/github.com/zalf-rpm/soybean-EU"
const maskColumn = "cropland"

func main() {
	gridSource := filepath.Join(projectpath, "stu_eu_layer_grid.csv")

	maskSource := filepath.Join(projectpath, "stu_eu_layer_grid_cropland.csv")

	extRow, extCol, minRow, minCol, gridSourceLookup := GetGridLookup(gridSource)
	maskLookup := getMaskGridLookup(maskSource)

	drawMaskedMaps(&gridSourceLookup, nil, &maskLookup,
		"%s_historical.asc",
		"crop_land_mask",
		extCol, extRow, minRow, minCol,
		"./",
		"crop land mask",
		"cropland in % ",
		"",
		"",
		nil, nil, nil, 1, 0,
		100, "", defaultOutFormat)

}
func defaultOutFormat(val int, factor float64) string {
	return strconv.Itoa(int(float64(val)*factor)) + " "
}

func drawMaskedMaps(gridSourceLookup *[][]int, simVal []int, maskLookup *map[GridCoord]float64, filenameFormat, filenameDescPart string, extCol, extRow, minRow, minCol int, asciiOutFolder, titleFormat, labelText string, colormap, colorlistType string, colorlist, cbarLabel []string, ticklist []float64, factor float64, minVal, maxVal int, minColor string, outFormat func(int, float64) string) {
	//simkey = treatmentNo, climateSenario, maturityGroup, comment
	gridFileName := fmt.Sprintf(filenameFormat, filenameDescPart)
	gridFilePath := filepath.Join(asciiOutFolder, gridFileName)
	file := writeAGridHeader(gridFilePath, extCol, extRow)

	formater := outFormat

	writeMaskedRows(file, extRow, extCol, simVal, gridSourceLookup, maskLookup, formater)

	file.Close()
	title := titleFormat
	writeMetaFile(gridFilePath, title, labelText, colormap, colorlistType, colorlist, cbarLabel, ticklist, factor, maxVal, minVal, minColor)
}

func writeMaskedRows(fout Fout, extRow, extCol int, simGrid []int, gridSourceLookup *[][]int, irrLookup *map[GridCoord]float64, outFormat func(int, float64) string) {
	for row := 0; row < extRow; row++ {
		for col := 0; col < extCol; col++ {
			refID := (*gridSourceLookup)[row][col]
			if refID > 0 {
				if val, ok := (*irrLookup)[GridCoord{row, col}]; ok {
					if simGrid != nil {
						fout.Write(outFormat(simGrid[refID-1], val))
					} else {
						fout.Write(outFormat(100, val))
					}
				} else {
					fout.Write("0")
				}
				fout.Write(" ")
			} else {
				fout.Write("-9999 ")
			}
		}
		fout.Write("\n")
	}
}

func writeAGridHeader(name string, nCol, nRow int) (fout Fout) {
	cornerX := 0.0
	cornery := 0.0
	cellsize := 1.0
	// create an ascii file, which contains the header
	makeDir(name)
	file, err := os.OpenFile(name+".gz", os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0600)
	if err != nil {
		log.Fatal(err)
	}

	gfile := gzip.NewWriter(file)
	fwriter := bufio.NewWriter(gfile)
	fout = Fout{file, gfile, fwriter}

	fout.Write(fmt.Sprintf("ncols %d\n", nCol))
	fout.Write(fmt.Sprintf("nrows %d\n", nRow))
	fout.Write(fmt.Sprintf("xllcorner     %f\n", cornerX))
	fout.Write(fmt.Sprintf("yllcorner     %f\n", cornery))
	fout.Write(fmt.Sprintf("cellsize      %f\n", cellsize))
	fout.Write(fmt.Sprintf("NODATA_value  %d\n", NONEVALUE))

	return fout
}

func writeMetaFile(gridFilePath, title, labeltext, colormap, colorlistType string, colorlist []string, cbarLabel []string, ticklist []float64, factor float64, maxValue, minValue int, minColor string) {
	metaFilePath := gridFilePath + ".meta"
	makeDir(metaFilePath)
	file, err := os.OpenFile(metaFilePath, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0600)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()
	file.WriteString(fmt.Sprintf("title: '%s'\n", title))
	file.WriteString("yTitle: 0.88\n")
	file.WriteString("xTitle: 0.05\n")
	file.WriteString("removeEmptyColumns: True\n")
	file.WriteString(fmt.Sprintf("labeltext: '%s'\n", labeltext))
	if colormap != "" {
		file.WriteString(fmt.Sprintf("colormap: '%s'\n", colormap))
	}
	if colorlist != nil {
		file.WriteString("colorlist: \n")
		for _, item := range colorlist {
			file.WriteString(fmt.Sprintf(" - '%s'\n", item))
		}
	}
	if cbarLabel != nil {
		file.WriteString("cbarLabel: \n")
		for _, cbarItem := range cbarLabel {
			file.WriteString(fmt.Sprintf(" - '%s'\n", cbarItem))
		}
	}
	if ticklist != nil {
		file.WriteString("ticklist: \n")
		for _, tick := range ticklist {
			file.WriteString(fmt.Sprintf(" - %f\n", tick))
		}
	}
	if len(colorlistType) > 0 {
		file.WriteString(fmt.Sprintf("colorlisttype: %s\n", colorlistType))
	}
	file.WriteString(fmt.Sprintf("factor: %f\n", factor))
	if maxValue != NONEVALUE {
		file.WriteString(fmt.Sprintf("maxValue: %d\n", maxValue))
	}
	if minValue != NONEVALUE {
		file.WriteString(fmt.Sprintf("minValue: %d\n", minValue))
	}
	if len(minColor) > 0 {
		file.WriteString(fmt.Sprintf("minColor: %s\n", minColor))
	}
}

// GetGridLookup ..
func GetGridLookup(gridsource string) (rowExt, colExt, rowMin, colMin int, lookupGrid [][]int) {
	colExt = 0
	rowExt = 0
	lookup := make(map[int64][]GridCoord)

	sourcefile, err := os.Open(gridsource)
	if err != nil {
		log.Fatal(err)
	}
	defer sourcefile.Close()
	firstLine := true
	colID := -1
	rowID := -1
	refID := -1
	scanner := bufio.NewScanner(sourcefile)
	for scanner.Scan() {
		line := scanner.Text()
		tokens := strings.Split(line, ",")
		if firstLine {
			firstLine = false
			for index, token := range tokens {
				if token == "Column_" {
					colID = index
				}
				if token == "Row" {
					rowID = index
				}
				if token == "soil_ref" {
					refID = index
				}
			}
		} else {
			col, _ := strconv.ParseInt(tokens[colID], 10, 64)
			row, _ := strconv.ParseInt(tokens[rowID], 10, 64)
			ref, _ := strconv.ParseInt(tokens[refID], 10, 64)
			if int(col) > colExt {
				colExt = int(col)
			}
			if int(row) > rowExt {
				rowExt = int(row)
			}
			if _, ok := lookup[ref]; !ok {
				lookup[ref] = make([]GridCoord, 0, 1)
			}
			lookup[ref] = append(lookup[ref], GridCoord{int(row), int(col)})
		}
	}
	lookupGrid = newGrid(rowExt, colExt, NONEVALUE)
	colMin = colExt
	rowMin = rowExt
	for ref, coord := range lookup {
		for _, rowCol := range coord {
			lookupGrid[rowCol.row-1][rowCol.col-1] = int(ref)
			if rowCol.col < colMin {
				colMin = rowCol.col
			}
			if rowCol.row < rowMin {
				rowMin = rowCol.row
			}
		}
	}

	return rowExt, colExt, rowMin, colMin, lookupGrid
}

func getMaskGridLookup(gridsource string) map[GridCoord]float64 {
	lookup := make(map[GridCoord]float64)

	sourcefile, err := os.Open(gridsource)
	if err != nil {
		log.Fatal(err)
	}
	defer sourcefile.Close()
	firstLine := true
	colID := -1
	rowID := -1
	maskID := -1
	scanner := bufio.NewScanner(sourcefile)
	for scanner.Scan() {
		line := scanner.Text()
		tokens := strings.Split(line, ",")
		if firstLine {
			firstLine = false
			// Column,Row,latitude,longitude,irrigation
			for index, token := range tokens {
				if token == "Column" {
					colID = index
				}
				if token == "Row" {
					rowID = index
				}
				if token == maskColumn {
					maskID = index
				}
			}
		} else {
			col, _ := strconv.ParseInt(tokens[colID], 10, 64)
			row, _ := strconv.ParseInt(tokens[rowID], 10, 64)
			mask, _ := strconv.ParseFloat(tokens[maskID], 64)
			if mask > 0 {
				lookup[GridCoord{int(row), int(col)}] = mask
			}
		}
	}
	return lookup
}

// GridCoord tuple of positions
type GridCoord struct {
	row int
	col int
}

func newGrid(extRow, extCol, defaultVal int) [][]int {
	grid := make([][]int, extRow)
	for r := 0; r < extRow; r++ {
		grid[r] = make([]int, extCol)
		for c := 0; c < extCol; c++ {
			grid[r][c] = defaultVal
		}
	}
	return grid
}

// Fout combined file writer
type Fout struct {
	file    *os.File
	gfile   *gzip.Writer
	fwriter *bufio.Writer
}

// Write string to zip file
func (f Fout) Write(s string) {
	f.fwriter.WriteString(s)
}

// Close file writer
func (f Fout) Close() {
	f.fwriter.Flush()
	// Close the gzip first.
	f.gfile.Close()
	f.file.Close()
}

func makeDir(outPath string) {
	dir := filepath.Dir(outPath)
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		if err := os.MkdirAll(dir, os.ModePerm); err != nil {
			log.Fatalf("ERROR: Failed to generate output path %s :%v", dir, err)
		}
	}
}

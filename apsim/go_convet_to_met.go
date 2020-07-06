package main

import (
	"bufio"
	"errors"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

const lineFmt = "%3d       %4d          %5.2f     %5.1f     %5.1f     %5.f     %5d\n"

// ConvertMonicaToMet convert weather files from monica format to apsim met format
func ConvertMonicaToMet(folderIn, folderOut, project, seperator string, co2 int) error {

	inputpath, err := filepath.Abs(folderIn)
	if err != nil {
		return err
	}
	outpath, err := filepath.Abs(folderOut)
	if err != nil {
		return err
	}

	projectpath, err := filepath.Abs(project)
	if err != nil {
		return err
	}
	//read long/lat from project files
	longLatfiles := []string{"missingregions.csv", "gridcells_altitude_ZALF-DK94-DK59.csv"}
	gridLatLonMap, err := extractLatLong(seperator, projectpath, longLatfiles)
	if err != nil {
		return err
	}
	fileCounter := 0
	// walk folder
	err = filepath.Walk(inputpath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			fmt.Printf("prevent panic by handling failure accessing a path %q: %v\n", path, err)
			return err
		}
		if !info.IsDir() && strings.HasSuffix(info.Name(), ".csv") {

			filename := strings.TrimSuffix(info.Name(), ".csv") + ".prn"
			fulloutpath := filepath.Join(outpath, strings.TrimPrefix(filepath.Dir(path), inputpath), filename)
			fileCounter++
			calcAnbAmplMeanMthTemp := annualAmplitudeMeanMonthlyTemperature()
			outLines := make([]string, 0, 11323)
			file, err := os.Open(path)
			if err != nil {
				return err
			}
			defer file.Close()
			scanner := bufio.NewScanner(file)
			// scrip the first 2 lines
			if ok := scanner.Scan(); !ok {
				return scanner.Err()
			}
			headerLine := scanner.Text()
			columns := strings.Split(headerLine, seperator)
			columnMap := make(map[string]int, len(columns))
			for i := 0; i < len(columns); i++ {
				columnMap[columns[i]] = i
			}
			var annualAmplitude, annualAverageAmbientTemp float64
			// skip units
			scanner.Scan()
			// read all lines
			for scanner.Scan() {
				line := scanner.Text()
				tokens := strings.Split(line, seperator)
				date, err := time.Parse("2006-01-02", tokens[columnMap["iso-date"]])
				if err != nil {
					return err
				}
				tmin, err := strconv.ParseFloat(tokens[columnMap["tmin"]], 64)
				if err != nil {
					return err
				}
				tavg, err := strconv.ParseFloat(tokens[columnMap["tavg"]], 64)
				if err != nil {
					return err
				}
				tmax, err := strconv.ParseFloat(tokens[columnMap["tmax"]], 64)
				if err != nil {
					return err
				}
				precip, err := strconv.ParseFloat(tokens[columnMap["precip"]], 64)
				if err != nil {
					return err
				}
				globrad, err := strconv.ParseFloat(tokens[columnMap["globrad"]], 64)
				if err != nil {
					return err
				}
				day := date.YearDay()
				// calculate   Annual amplitude in mean monthly temperature
				// calculate Annual average ambient temperature
				annualAmplitude, annualAverageAmbientTemp = calcAnbAmplMeanMthTemp(tavg, &date)
				year := date.Year()
				outLines = append(outLines, fmt.Sprintf(lineFmt, day, year, globrad, tmax, tmin, precip, co2))
			}

			tokens := strings.Split(info.Name(), "_")
			rolCol := tokens[0] + "_" + tokens[1]
			latitude, longitude := gridLatLonMap[rolCol][0], gridLatLonMap[rolCol][1]
			lat, err := strconv.ParseFloat(latitude, 64)
			if err != nil {
				return err
			}
			long, err := strconv.ParseFloat(longitude, 64)
			if err != nil {
				return err
			}
			header := createMetFileHeader(lat, long, annualAverageAmbientTemp, annualAmplitude)
			// copy folder structure
			makeDir(fulloutpath)
			fmt.Println(fulloutpath)
			outFile, err := os.OpenFile(fulloutpath, os.O_TRUNC|os.O_CREATE|os.O_WRONLY, 0600)
			if err != nil {
				return err
			}
			writer := bufio.NewWriter(outFile)
			for _, str := range header {
				writer.WriteString(str)
			}
			for _, str := range outLines {
				writer.WriteString(str)
			}
			writer.Flush()
			outFile.Close()
		}
		return nil
	})

	return err
}
func annualAmplitudeMeanMonthlyTemperature() func(float64, *time.Time) (float64, float64) {
	var currentMonth time.Month = 1
	currentMonthDays := 0
	currentYearDays := 0
	sumCurrentMonthAvg := 0.0
	meanMonthlyTemperature := 0.0
	meanMonthlyTemperatureMin := 0.0
	meanMonthlyTemperatureMax := 0.0
	annualAmplitude := 0.0 // over all years? average over years?
	yearAmplitude := 0.0
	numYearAmplitude := 0
	annualAverageAmbientTemp := 0.0
	sumMeanMonthlyTemperature := 0.0
	monthCounted := 0

	return func(dayTavg float64, date *time.Time) (float64, float64) {
		if currentMonth != date.Month() {
			if meanMonthlyTemperature < meanMonthlyTemperatureMin {
				meanMonthlyTemperatureMin = meanMonthlyTemperature
			}
			if meanMonthlyTemperature > meanMonthlyTemperatureMax {
				meanMonthlyTemperatureMax = meanMonthlyTemperature
			}
			sumMeanMonthlyTemperature = sumMeanMonthlyTemperature + meanMonthlyTemperature
			monthCounted++
			annualAverageAmbientTemp = sumMeanMonthlyTemperature / float64(monthCounted)
			currentMonth = date.Month()
			currentMonthDays = 0
			sumCurrentMonthAvg = 0
			meanMonthlyTemperature = 0
		}

		// add to current month
		currentMonthDays++
		currentYearDays++
		sumCurrentMonthAvg = sumCurrentMonthAvg + dayTavg
		meanMonthlyTemperature = sumCurrentMonthAvg / float64(currentMonthDays)

		// calculate annual Amplitude on last DOY
		if date.Equal(time.Date(date.Year(), time.December, 31, 0, 0, 0, 0, time.UTC)) {
			// previous year should have at least 365 days
			if currentYearDays >= 365 {
				yearAmplitude = yearAmplitude + (meanMonthlyTemperatureMax - meanMonthlyTemperatureMin)
				numYearAmplitude++
				annualAmplitude = yearAmplitude / float64(numYearAmplitude)
			}
			meanMonthlyTemperatureMin = 1000
			meanMonthlyTemperatureMax = -1000
			currentYearDays = 0
		}

		//annualAmplitude = (meanMonthlyTemperatureMax - meanMonthlyTemperatureMin)
		return annualAmplitude, annualAverageAmbientTemp
	}
}

func createMetFileHeader(latitude, longitude, tav, amp float64) (header []string) {
	header = []string{
		"[weather.met.weather]\n",
		fmt.Sprintf("latitude = %0.1f  (DECIMAL DEGREES)\n", latitude),
		fmt.Sprintf("longitude = %0.1f  (DECIMAL DEGREES)\n", longitude),
		fmt.Sprintf("tav= %0.13f   (oC) ! Annual average ambient temperature\n", tav),
		fmt.Sprintf("amp= %0.13f   (oC) ! Annual amplitude in mean monthly temperature\n", amp),
		"!\n",
		"Day       Year           radn      maxT      minT      rain     CO2\n",
		"()        ()         (MJ/m^2)      (oC)      (oC)      (mm)     (ppm)\n"}

	return header
}

func makeDir(outPath string) {
	dir := filepath.Dir(outPath)
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		if err := os.MkdirAll(dir, os.ModePerm); err != nil {
			log.Fatalf("ERROR: Failed to generate output path %s :%v", dir, err)
		}
	}
}

func extractLatLong(seperator, projectpath string, files []string) (map[string][2]string, error) {

	entries := make(map[string][2]string)
	for _, filename := range files {
		path := filepath.Join(projectpath, filename)
		file, err := os.Open(path)
		if err != nil {
			return nil, err
		}
		defer file.Close()
		scanner := bufio.NewScanner(file)
		if ok := scanner.Scan(); !ok {
			return nil, errors.New("failed to read header")
		}
		header := readHeader(scanner.Text(), seperator)

		for scanner.Scan() {
			rowCol, lat, long := loadLine(scanner.Text(), seperator, header)
			entries[rowCol] = [2]string{lat, long}
		}
	}
	return entries, nil
}

func readHeader(line, seperator string) map[string]int {
	//read header
	//"GRID_NO","LATITUDE","LONGITUDE","ALTITUDE","DAY","TEMPERATURE_MAX","TEMPERATURE_MIN","TEMPERATURE_AVG","WINDSPEED","VAPOURPRESSURE","PRECIPITATION","RADIATION"
	//GRID_NO,LATITUDE,LONGITUDE,ALTITUDE
	tokens := strings.Split(line, seperator)
	outDic := make(map[string]int)
	i := -1
	for _, token := range tokens {
		token = strings.Trim(token, "\" ")
		i++
		if token == "LATITUDE" {
			outDic["lat"] = i
		}
		if token == "LONGITUDE" {
			outDic["lon"] = i
		}
		if token == "GRID_NO" {
			outDic["grid_no"] = i
		}
		if token == "ALTITUDE" {
			outDic["alti"] = i
		}
	}
	return outDic
}

func loadLine(line, seperator string, header map[string]int) (rowCol, lat, long string) {
	//read relevant content from line
	tokens := strings.Split(line, seperator)
	gridIdx := tokens[header["grid_no"]]
	row := gridIdx[:len(gridIdx)-3]
	col := gridIdx[len(gridIdx)-3:]
	rowCol = row + "_" + col
	long = tokens[header["lon"]]
	lat = tokens[header["lat"]]

	return rowCol, lat, long
}

package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"time"
)

const filename = "missing.txt"
const rscript1 = "scriptRotaClusterSM.R"
const rscript2 = "scriptRotaClusterMS.R"
const cmdline = "exec -B %s:/home/raynalh/scratch,%s:/home/raynalh/scratch/climate singularityR3.6.3_08092020dev.simg Rscript "

// singularity exec -B \
// $HOMEFOLDER:/home/raynalh/scratch,$CLIMATE_PATH:/home/raynalh/scratch/climate \
// singularityR3.6.3_08092020dev.simg \
// Rscript scriptRotaCluster${SCRIPT_TYPE}.R $INDEX

// # alway sleep to avoid generation conflict
// sleep 10

func main() {

	climatePath := flag.String("climatePath", "", "path to climate folder")
	homePath := flag.String("homePath", "", "path to home")
	concurrent := flag.Int("concurrent", 10, "concurrent processes")
	start := flag.Int("start", 1, "start line")
	end := flag.Int("end", 99367, "end line including")

	flag.Parse()

	idList := make([]string, 0, *end+1-*start)
	// read file with missing sims
	simsFile, err := os.Open(filename)
	if err == nil {
		scanner := bufio.NewScanner(simsFile)
		linecounter := 0
		for scanner.Scan() {
			linecounter++
			id := scanner.Text()
			id = strings.TrimSpace(id)
			if linecounter < *start {
				continue
			}
			if linecounter > *end {
				break
			}
			idList = append(idList, id)
		}
		simsFile.Close()
	} else {
		// missing.txt not found - generate ids
		fmt.Printf("missing.txt not found \n generating numbers from %d to %d ", *start, *end)
		for id := *start; id <= *end; id++ {
			idList = append(idList, strconv.Itoa(id))
		}
	}
	call := fmt.Sprintf(cmdline, *homePath, *climatePath)

	runIDList(*homePath, call, rscript1, idList, *concurrent)
	runIDList(*homePath, call, rscript2, idList, *concurrent)
}

func runIDList(workdir, call, rscript string, idList []string, concurrent int) {
	// start active runs for number of concurrentOperations
	// when an active run is finished, start a follow up run
	logOutputChan := make(chan string)
	resultChannel := make(chan string)
	var activeRuns int
	for _, id := range idList {
		for activeRuns == concurrent {
			select {
			case <-resultChannel:
				activeRuns--
			case log := <-logOutputChan:
				fmt.Println(log)
			}
		}

		if activeRuns < concurrent {
			activeRuns++
			fmt.Printf("[%v] started\n", id)
			go doCall(workdir, call, rscript, id, resultChannel, logOutputChan)
			time.Sleep(10 * time.Second)
		}
	}

	// fetch output of last runs
	for activeRuns > 0 {
		select {
		case <-resultChannel:
			activeRuns--
		case log := <-logOutputChan:
			fmt.Println(log)
		}
	}
}

func doCall(workingDir, cmdline, rscript, id string, outResult, logOutputChan chan string) {

	var cmd *exec.Cmd
	// test: create for command
	args := strings.Fields(cmdline)
	args = append(args, rscript, id)

	cmd = exec.Command("singularity", args...)
	cmd.Dir = workingDir

	// create output pipe
	cmdOut, err := cmd.StdoutPipe()
	if err != nil {
		cmdresult := fmt.Sprintf(`%s Process failed to generate out pipe: %s`, id, err)
		outResult <- cmdresult
		return
	}

	// run command
	err = cmd.Start()
	if err != nil {
		cmdresult := fmt.Sprintf(`%s Process failed to start: %s`, id, err)
		outResult <- cmdresult
		return
	}

	// scan for output
	outScanner := bufio.NewScanner(cmdOut)
	outScanner.Split(bufio.ScanLines)
	c1 := make(chan bool, 1)
	go func() {
		for outScanner.Scan() {
			text := outScanner.Text()
			logOutputChan <- id + "" + text
			c1 <- true
		}
		c1 <- false
	}()

	// wait until programm is finished
	err = cmd.Wait()
	if err != nil {
		cmdresult := fmt.Sprintf(`%s Execution failed with error: %s`, id, err)
		outResult <- cmdresult
		return
	}

	cmdresult := id + " Success"
	outResult <- cmdresult
}

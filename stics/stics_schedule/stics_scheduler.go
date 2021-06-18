package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"
	"time"
)

var concurrentOperations uint16 = 10 // number of paralell processes
const filename = "missing.txt"
const rscript1 = "scriptRotaClusterSMGISS.R"
const rscript2 = "scriptRotaClusterMGISS.R"
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

	flag.Parse()

	// read file with missing sims
	simsFile, err := os.Open(filename)
	if err != nil {
		log.Fatal(err)
	}
	defer simsFile.Close()

	scanner := bufio.NewScanner(simsFile)

	call := fmt.Sprintf(cmdline, *homePath, *climatePath)
	// start active runs for number of concurrentOperations
	// when an active run is finished, start a follow up run
	logOutputChan := make(chan string)
	resultChannel := make(chan string)
	var activeRuns uint16
	for scanner.Scan() {

		id := scanner.Text()
		id = strings.TrimSpace(id)

		for activeRuns == concurrentOperations {
			select {
			case <-resultChannel:
				activeRuns--
			case log := <-logOutputChan:
				fmt.Println(log)
			}
		}

		if activeRuns < concurrentOperations {
			activeRuns++
			logID := fmt.Sprintf("[%v] started", id)
			fmt.Println(logID)
			go doCall(*homePath, call, rscript1, id, resultChannel, logOutputChan)
			time.Sleep(10 * time.Second)
			go doCall(*homePath, call, rscript2, id, resultChannel, logOutputChan)
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

#!/bin/bash -x
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=80
#SBATCH --partition=compute
#SBATCH --job-name=apsim_met
#SBATCH --time=01:00:00


# download go image
IMAGE_DIR_GO=~/singularity/other
SINGULARITY_GO_IMAGE=golang_1.14.4.sif
IMAGE_GO_PATH=${IMAGE_DIR_GO}/${SINGULARITY_GO_IMAGE}
mkdir -p $IMAGE_DIR_GO
if [ ! -e ${IMAGE_GO_PATH} ] ; then
echo "File '${IMAGE_GO_PATH}' not found"
cd $IMAGE_DIR_GO
singularity pull docker://golang:1.14.4
cd ~
fi
cd /beegfs/rpm/projects/apsim/projects/soybeanEU
singularity run ~/singularity/other/golang_1.14.4.sif go build -v -o metConversion


mkdir -p /beegfs/rpm/projects/apsim/projects/soybeanEU/met/0
mkdir -p /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/GFDL-CM3_45
mkdir -p /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/GISS-E2-R_45
mkdir -p /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/HadGEM2-ES_45
mkdir -p /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/MIROC5_45
mkdir -p /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/MPI-ESM-MR_45

./metConversion \
-source /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected/0 \
-output /beegfs/rpm/projects/apsim/projects/soybeanEU/met/0 \
-project /beegfs/rpm/projects/apsim/projects/soybeanEU/project_data \
-co2 360 &

./metConversion \
-source /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected/2/GFDL-CM3_45 \
-output /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/GFDL-CM3_45 \
-project /beegfs/rpm/projects/apsim/projects/soybeanEU/project_data \
-co2 499 &

./metConversion \
-source /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected/2/GISS-E2-R_45 \
-output /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/GISS-E2-R_45 \
-project /beegfs/rpm/projects/apsim/projects/soybeanEU/project_data \
-co2 499 &

./metConversion \
-source /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected/2/HadGEM2-ES_45 \
-output /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/HadGEM2-ES_45 \
-project /beegfs/rpm/projects/apsim/projects/soybeanEU/project_data \
-co2 499 &

./metConversion \
-source /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected/2/MIROC5_45 \
-output /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/MIROC5_45 \
-project /beegfs/rpm/projects/apsim/projects/soybeanEU/project_data \
-co2 499 &

./metConversion \
-source /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected/2/MPI-ESM-MR_45 \
-output /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/MPI-ESM-MR_45 \
-project /beegfs/rpm/projects/apsim/projects/soybeanEU/project_data \
-co2 499 &

wait
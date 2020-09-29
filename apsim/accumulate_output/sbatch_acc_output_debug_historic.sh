#!/bin/bash -x
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=80
#SBATCH --partition=compute
#SBATCH --job-name=apsim_accu
#SBATCH --time=24:00:00


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
cd /beegfs/rpm/projects/apsim/projects/soybeanEU/accumulate_output
singularity run ~/singularity/other/golang_1.14.4.sif go build -v -o accumulate_output


mkdir -p /beegfs/rpm/projects/apsim/projects/soybeanEU/out_transformed

./accumulate_output \
-in /beegfs/rpm/projects/apsim/projects/soybeanEU/out_0_0_0 \
-out /beegfs/rpm/projects/apsim/projects/soybeanEU/out_transformed \
-base ./base.csv \
-period 0 \
-sce 0_0 \
-co2 360 \
-concurrent 40 



wait
#!/bin/bash -x
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=80
#SBATCH --partition=compute
#SBATCH --job-name=stics_sschulz
#SBATCH --time=14-99:00:00
#SBATCH --output=missLegGapSched_%A.out
#SBATCH --error=missLegGapSched_%A.err

START=$1
END=$2
PARALLEL_JOBS=40
OUTPUT_FOLDER=$3

INTERNAL_OUTPUT_FOLDER=outputsLG
SOURCE_PATH=/beegfs/rpm/projects/stics/soybeanEU/scratch
OUT_PATH=/beegfs/rpm/projects/stics/soybeanEU/outputs
CLIMATE_PATH=/beegfs/rpm/projects/stics/soybeanEU/climate

DATE=`date +%Y-%d-%B_%H%M%S`
TEMPWORKFOLDER=/scratch/rpm/stics_${START}_${END}_TEMP_${DATE}
mkdir -p $TEMPWORKFOLDER

cp -a $SOURCE_PATH/. $TEMPWORKFOLDER

HOMEFOLDER=$TEMPWORKFOLDER

mkdir -p $HOMEFOLDER/$INTERNAL_OUTPUT_FOLDER
mkdir -p $HOMEFOLDER/log

cd ${HOMEFOLDER} 
SINGULARITY_HOME=${HOMEFOLDER}
export SINGULARITY_HOME

./stics_schedule -homePath $HOMEFOLDER -climatePath $CLIMATE_PATH -concurrent $PARALLEL_JOBS -start $START -end $END

mkdir -p $OUT_PATH/$OUTPUT_FOLDER
#mkdir -p $OUT_PATH/log

#cp -a $HOMEFOLDER/log/. $OUT_PATH/log
cp -a $HOMEFOLDER/$INTERNAL_OUTPUT_FOLDER/. $OUT_PATH/$OUTPUT_FOLDER

rm -rf $TEMPWORKFOLDER
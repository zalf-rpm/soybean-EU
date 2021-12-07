#!/bin/bash -x
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=80
#SBATCH --partition=compute
#SBATCH --job-name=apsim85accu
#SBATCH --time=48:00:00


mkdir -p /beegfs/rpm/projects/apsim/projects/soybeanEU/out_transformed

./accumulate_output \
-in /beegfs/rpm/projects/apsim/projects/soybeanEU/out_2_GFDL-CM3_85 \
-out /beegfs/rpm/projects/apsim/projects/soybeanEU/out_transformed \
-base ./base.csv \
-period 2 \
-sce GFDL-CM3_85 \
-co2 571 \
-concurrent 40 

./accumulate_output \
-in /beegfs/rpm/projects/apsim/projects/soybeanEU/out_2_GISS-E2-R_85 \
-out /beegfs/rpm/projects/apsim/projects/soybeanEU/out_transformed \
-base ./base.csv \
-period 2 \
-sce GISS-E2-R_85 \
-co2 571 \
-concurrent 40 

./accumulate_output \
-in /beegfs/rpm/projects/apsim/projects/soybeanEU/out_2_HadGEM2-ES_85 \
-out /beegfs/rpm/projects/apsim/projects/soybeanEU/out_transformed \
-base ./base.csv \
-period 2 \
-sce HadGEM2-ES_85 \
-co2 571 \
-concurrent 40 

./accumulate_output \
-in /beegfs/rpm/projects/apsim/projects/soybeanEU/out_2_MIROC5_85 \
-out /beegfs/rpm/projects/apsim/projects/soybeanEU/out_transformed \
-base ./base.csv \
-period 2 \
-sce MIROC5_85 \
-co2 571 \
-concurrent 40 

./accumulate_output \
-in /beegfs/rpm/projects/apsim/projects/soybeanEU/out_2_MPI-ESM-MR_85 \
-out /beegfs/rpm/projects/apsim/projects/soybeanEU/out_transformed \
-base ./base.csv \
-period 2 \
-sce MPI-ESM-MR_85 \
-co2 571 \
-concurrent 40 


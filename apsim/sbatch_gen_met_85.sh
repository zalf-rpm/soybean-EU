#!/bin/bash -x
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=80
#SBATCH --partition=compute
#SBATCH --job-name=apsim_met
#SBATCH --time=05:00:00


mkdir -p /beegfs/rpm/projects/apsim/projects/soybeanEU/met/0
mkdir -p /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/GFDL-CM3_85
mkdir -p /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/GISS-E2-R_85
mkdir -p /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/HadGEM2-ES_85
mkdir -p /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/MIROC5_85
mkdir -p /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/MPI-ESM-MR_85

./metConversion \
-source /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected2/0 \
-output /beegfs/rpm/projects/apsim/projects/soybeanEU/met/0 \
-project /beegfs/rpm/projects/apsim/projects/soybeanEU/setup/project_data \
-co2 360 &

./metConversion \
-source /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected2/2/GFDL-CM3_85 \
-output /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/GFDL-CM3_85 \
-project /beegfs/rpm/projects/apsim/projects/soybeanEU/setup/project_data \
-co2 571 &

./metConversion \
-source /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected2/2/GISS-E2-R_85 \
-output /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/GISS-E2-R_85 \
-project /beegfs/rpm/projects/apsim/projects/soybeanEU/setup/project_data \
-co2 571 &

./metConversion \
-source /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected2/2/HadGEM2-ES_85 \
-output /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/HadGEM2-ES_85 \
-project /beegfs/rpm/projects/apsim/projects/soybeanEU/setup/project_data \
-co2 571 &

./metConversion \
-source /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected2/2/MIROC5_85 \
-output /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/MIROC5_85 \
-project /beegfs/rpm/projects/apsim/projects/soybeanEU/setup/project_data \
-co2 571 &

./metConversion \
-source /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected2/2/MPI-ESM-MR_85 \
-output /beegfs/rpm/projects/apsim/projects/soybeanEU/met/2/MPI-ESM-MR_85 \
-project /beegfs/rpm/projects/apsim/projects/soybeanEU/setup/project_data \
-co2 571 &

wait
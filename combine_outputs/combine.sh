#!/bin/bash -x
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=80
#SBATCH --partition=compute
#SBATCH --job-name=comb_soy
#SBATCH --time=05:00:00

cd ~/go/src/github.com/soybean-EU/combine_outputs

./combine_outputs \
-path Cluster \
-source1 /beegfs/rpm/projects/monica/out/sschulz_1239_2020-29-May_172516 \
-source2 /beegfs/rpm/projects/apsim/projects/soybeanEU/out_transformed/ \
-project /beegfs/rpm/projects/monica/project/soybeanEU \
-climate /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected \
-out .

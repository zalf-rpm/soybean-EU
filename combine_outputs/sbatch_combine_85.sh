#!/bin/bash -x
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=80
#SBATCH --partition=compute
#SBATCH --job-name=85comb_soy
#SBATCH --time=05:00:00

cd ~/go/src/github.com/soybean-EU/combine_outputs

./combine_outputs \
-path Cluster \
-source1 /beegfs/rpm/projects/monica/out/sschulz_2979_2021-15-December_193849 \
-source2 /beegfs/rpm/projects/apsim/projects/soybeanEU/out_transformed_85/ \
-source3 /beegfs/rpm/projects/hermes/SoybeanEU/setup/acc/85 \
-source4 /beegfs/rpm/projects/stics/out_SoybeanEU_06_01_2022_85/merged_1 \
-harvest4 30 \
-cut1 15 \
-cut2 15 \
-cut3 15 \
-cut4 15 \
-project /beegfs/rpm/projects/monica/project/soybeanEU \
-climate /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected2 \
-out ./cut_date_15_climS_85

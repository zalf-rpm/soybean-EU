#!/bin/bash -x
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=80
#SBATCH --partition=compute
#SBATCH --job-name=45comb_soy
#SBATCH --time=05:00:00

cd ~/go/src/github.com/soybean-EU/combine_outputs

./combine_outputs \
-path Cluster \
-source1 /beegfs/rpm/projects/monica/out/sschulz_2043_2021-08-January_111051 \
-source2 /beegfs/rpm/projects/apsim/projects/soybeanEU/out_transformed_45/ \
-source3 /beegfs/rpm/projects/hermes/SoybeanEU/acc/ \
-source4 /beegfs/rpm/projects/stics/out_SoybeanEU_24_01_2022_45/merged_1/ \
-harvest4 30 \
-cut1 15 \
-cut2 15 \
-cut3 15 \
-cut4 15 \
-project /beegfs/rpm/projects/monica/project/soybeanEU \
-climate /beegfs/common/data/climate/macsur_european_climate_scenarios_v3/testing/corrected2 \
-out ./cut_date_15_climS_45

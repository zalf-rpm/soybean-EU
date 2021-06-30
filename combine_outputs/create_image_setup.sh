#!/bin/bash +x 
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --partition=compute
#SBATCH --job-name=prepare_combine_soyEU
#SBATCH --time=00:10:00

mkdir -p ./ascii_source
cp ./image-setup.yml ./ascii_source/image-setup.yml 
cp ./asciigrid_combined/dev/dev_max_yield_historical.asc.gz ./ascii_source/density_max_yield_historical.asc.gz
cp ./asciigrid_combined/dev/dev_max_yield_future.asc.gz ./ascii_source/density_max_yield_future.asc.gz
cp ./density_max_yield_historical.asc.meta ./ascii_source/density_max_yield_historical.asc.meta
cp ./density_max_yield_future.asc.meta ./ascii_source/density_max_yield_future.asc.meta

cp ./density_short_season_future.asc.meta ./ascii_source/density_short_season_future.asc.meta
cp ./density_short_season_historical.asc.meta ./ascii_source/density_short_season_historical.asc.meta
cp ./density_drought_risk_future.asc.meta ./ascii_source/density_drought_risk_future.asc.meta
cp ./density_drought_risk_historical.asc.meta ./ascii_source/density_drought_risk_historical.asc.meta
cp ./density_000_historical.asc.meta ./ascii_source/density_000_historical.asc.meta
cp ./density_000_future.asc.meta ./ascii_source/density_000_future.asc.meta
cp ./density_II_historical.asc.meta ./ascii_source/density_II_historical.asc.meta
cp ./density_II_future.asc.meta ./ascii_source/density_II_future.asc.meta

cp ./asciigrid_combined/dev/mg_II_historical.asc.gz ./ascii_source/density_II_historical.asc.gz
cp ./asciigrid_combined/dev/mg_II_future.asc.gz ./ascii_source/density_II_future.asc.gz
cp ./asciigrid_combined/dev/mg_000_historical.asc.gz ./ascii_source/density_000_historical.asc.gz
cp ./asciigrid_combined/dev/mg_000_future.asc.gz ./ascii_source/density_000_future.asc.gz
cp ./asciigrid_combined/dev/dev_short_season_historical.asc.gz ./ascii_source/density_short_season_historical.asc.gz 
cp ./asciigrid_combined/dev/dev_short_season_future.asc.gz ./ascii_source/density_short_season_future.asc.gz 
cp ./asciigrid_combined/dev/dev_drought_risk_historical.asc.gz ./ascii_source/density_drought_risk_historical.asc.gz 
cp ./asciigrid_combined/dev/dev_drought_risk_future.asc.gz ./ascii_source/density_drought_risk_future.asc.gz 

cp ./asciigrid_combined/dev/irrgated_areas.asc.meta ./ascii_source/irrgated_areas.asc.meta
cp ./asciigrid_combined/dev/irrgated_areas.asc.gz ./ascii_source/irrgated_areas.asc.gz

cp ./asciigrid_combined/dev/dev_max_yield_historical.asc.meta ./ascii_source/dev_max_yield_historical.asc.meta
cp ./asciigrid_combined/dev/dev_max_yield_historical.asc.gz ./ascii_source/dev_max_yield_historical.asc.gz
cp ./asciigrid_combined/dev/dev_max_yield_future.asc.meta ./ascii_source/dev_max_yield_future.asc.meta
cp ./asciigrid_combined/dev/dev_max_yield_future.asc.gz ./ascii_source/dev_max_yield_future.asc.gz
cp ./asciigrid_combined/dev/dev_maturity_groups_historical.asc.meta ./ascii_source/dev_maturity_groups_historical.asc.meta
cp ./asciigrid_combined/dev/dev_maturity_groups_historical.asc.gz ./ascii_source/dev_maturity_groups_historical.asc.gz
cp ./asciigrid_combined/dev/dev_maturity_groups_future.asc.meta ./ascii_source/dev_maturity_groups_future.asc.meta
cp ./asciigrid_combined/dev/dev_maturity_groups_future.asc.gz ./ascii_source/dev_maturity_groups_future.asc.gz
cp ./asciigrid_combined/dev/dev_allRisks_historical.asc.meta ./ascii_source/dev_allRisks_historical.asc.meta
cp ./asciigrid_combined/dev/dev_allRisks_historical.asc.gz ./ascii_source/dev_allRisks_historical.asc.gz
cp ./asciigrid_combined/dev/dev_allRisks_future.asc.meta ./ascii_source/dev_allRisks_future.asc.meta
cp ./asciigrid_combined/dev/dev_allRisks_future.asc.gz ./ascii_source/dev_allRisks_future.asc.gz

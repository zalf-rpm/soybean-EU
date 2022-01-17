#!/bin/bash +x 
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --partition=compute
#SBATCH --job-name=prepare_combine_soyEU
#SBATCH --time=00:10:00

TARGETFOLDER=../asciigrids_debug/ascii_source
SOURCEFOLDER=./cut_date_15_climS_85
SOURCEFOLDER45=./cut_date_15_climS_45

mkdir -p ${TARGETFOLDER}
cp ./with_85/image-setup_85.yml ${TARGETFOLDER}/image-setup.yml 
# violin yield
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_max_yield_historical.asc.gz ${TARGETFOLDER}/violin_max_yield_historical.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_max_yield_future.asc.gz ${TARGETFOLDER}/violin_max_yield_future85.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_max_yield_future.asc.gz ${TARGETFOLDER}/violin_max_yield_future45.asc.gz
cp ./with_85/violin_max_yield_historical.asc.meta ${TARGETFOLDER}/violin_max_yield_historical.asc.meta
cp ./with_85/violin_max_yield_future85.asc.meta ${TARGETFOLDER}/violin_max_yield_future85.asc.meta
cp ./with_85/violin_max_yield_future45.asc.meta ${TARGETFOLDER}/violin_max_yield_future45.asc.meta

# maturity violin plots
cp ./with_85/violin_maturity_groups_historical.asc.meta ${TARGETFOLDER}/violin_maturity_groups_historical.asc.meta
cp ./with_85/violin_maturity_groups_future85.asc.meta ${TARGETFOLDER}/violin_maturity_groups_future85.asc.meta
cp ./with_85/violin_maturity_groups_future45.asc.meta ${TARGETFOLDER}/violin_maturity_groups_future45.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_historical.asc.gz ${TARGETFOLDER}/violin_maturity_groups_historical.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_future.asc.gz ${TARGETFOLDER}/violin_maturity_groups_future85.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_maturity_groups_future.asc.gz ${TARGETFOLDER}/violin_maturity_groups_future45.asc.gz

# risk violin plots
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_short_season_historical.asc.gz ${TARGETFOLDER}/violin_short_season_historical.asc.gz 
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_short_season_future.asc.gz ${TARGETFOLDER}/violin_short_season_future85.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_short_season_future.asc.gz ${TARGETFOLDER}/violin_short_season_future45.asc.gz
cp ./with_85/violin_short_season_historical.asc.meta ${TARGETFOLDER}/violin_short_season_historical.asc.meta
cp ./with_85/violin_short_season_future85.asc.meta ${TARGETFOLDER}/violin_short_season_future85.asc.meta
cp ./with_85/violin_short_season_future45.asc.meta ${TARGETFOLDER}/violin_short_season_future45.asc.meta

cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_drought_risk_historical.asc.gz ${TARGETFOLDER}/violin_drought_risk_historical.asc.gz 
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_drought_risk_future.asc.gz ${TARGETFOLDER}/violin_drought_risk_future85.asc.gz 
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_drought_risk_future.asc.gz ${TARGETFOLDER}/violin_drought_risk_future45.asc.gz
cp ./with_85/violin_drought_risk_historical.asc.meta ${TARGETFOLDER}/violin_drought_risk_historical.asc.meta
cp ./with_85/violin_drought_risk_future85.asc.meta ${TARGETFOLDER}/violin_drought_risk_future85.asc.meta
cp ./with_85/violin_drought_risk_future45.asc.meta ${TARGETFOLDER}/violin_drought_risk_future45.asc.meta

# risk harvest rain 
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_harvest_rain_historical.asc.gz ${TARGETFOLDER}/violin_harvest_rain_historical.asc.gz 
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_harvest_rain_future.asc.gz ${TARGETFOLDER}/violin_harvest_rain_future85.asc.gz 
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_harvest_rain_future.asc.gz ${TARGETFOLDER}/violin_harvest_rain_future45.asc.gz
cp ./with_85/violin_harvest_rain_historical.asc.meta ${TARGETFOLDER}/violin_harvest_rain_historical.asc.meta
cp ./with_85/violin_harvest_rain_future85.asc.meta ${TARGETFOLDER}/violin_harvest_rain_future85.asc.meta
cp ./with_85/violin_harvest_rain_future45.asc.meta ${TARGETFOLDER}/violin_harvest_rain_future45.asc.meta

# risk cold spell 
cp ${SOURCEFOLDER}/asciigrid_combined/dev/coldSpell_historical.asc.gz ${TARGETFOLDER}/violin_coldSpell_historical.asc.gz 
cp ${SOURCEFOLDER}/asciigrid_combined/dev/coldSpell_future.asc.gz ${TARGETFOLDER}/violin_coldSpell_future85.asc.gz 
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/coldSpell_future.asc.gz ${TARGETFOLDER}/violin_coldSpell_future45.asc.gz
cp ./with_85/violin_coldSpell_historical.asc.meta ${TARGETFOLDER}/violin_coldSpell_historical.asc.meta
cp ./with_85/violin_coldSpell_future85.asc.meta ${TARGETFOLDER}/violin_coldSpell_future85.asc.meta
cp ./with_85/violin_coldSpell_future45.asc.meta ${TARGETFOLDER}/violin_coldSpell_future45.asc.meta


# irrigation map
cp ${SOURCEFOLDER}/asciigrid_combined/dev/irrgated_areas.asc.meta ${TARGETFOLDER}/irrgated_areas.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/irrgated_areas.asc.gz ${TARGETFOLDER}/irrgated_areas.asc.gz
# all yield heatmap
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_max_yield_historical.asc.meta ${TARGETFOLDER}/dev_max_yield_historical.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_max_yield_historical.asc.gz ${TARGETFOLDER}/dev_max_yield_historical.asc.gz
sed -i 's/title: .*/title: A/g' ${TARGETFOLDER}/dev_max_yield_historical.asc.meta

cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_max_yield_future.asc.meta ${TARGETFOLDER}/dev_max_yield_future85.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_max_yield_future.asc.gz ${TARGETFOLDER}/dev_max_yield_future85.asc.gz
sed -i 's/title: .*/title: C/g' ${TARGETFOLDER}/dev_max_yield_future85.asc.meta

cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_max_yield_future.asc.meta ${TARGETFOLDER}/dev_max_yield_future45.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_max_yield_future.asc.gz ${TARGETFOLDER}/dev_max_yield_future45.asc.gz
sed -i 's/title: .*/title: B/g' ${TARGETFOLDER}/dev_max_yield_future45.asc.meta

# all maturity group heatmaps
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_historical.asc.meta ${TARGETFOLDER}/dev_maturity_groups_historical.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_historical.asc.gz ${TARGETFOLDER}/dev_maturity_groups_historical.asc.gz
sed -i 's/title: .*/title: A/g' ${TARGETFOLDER}/dev_maturity_groups_historical.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_future.asc.meta ${TARGETFOLDER}/dev_maturity_groups_future85.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_future.asc.gz ${TARGETFOLDER}/dev_maturity_groups_future85.asc.gz
sed -i 's/title: .*/title: C/g' ${TARGETFOLDER}/dev_maturity_groups_future85.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_maturity_groups_future.asc.meta ${TARGETFOLDER}/dev_maturity_groups_future45.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_maturity_groups_future.asc.gz ${TARGETFOLDER}/dev_maturity_groups_future45.asc.gz
sed -i 's/title: .*/title: B/g' ${TARGETFOLDER}/dev_maturity_groups_future45.asc.meta
# all risk heatmaps
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_allRisks_historical.asc.meta ${TARGETFOLDER}/dev_allRisks_historical.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_allRisks_historical.asc.gz ${TARGETFOLDER}/dev_allRisks_historical.asc.gz
sed -i 's/title: .*/title: A/g' ${TARGETFOLDER}/dev_allRisks_historical.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_allRisks_future.asc.meta ${TARGETFOLDER}/dev_allRisks_future85.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_allRisks_future.asc.gz ${TARGETFOLDER}/dev_allRisks_future85.asc.gz
sed -i 's/title: .*/title: C/g' ${TARGETFOLDER}/dev_allRisks_future85.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_allRisks_future.asc.meta ${TARGETFOLDER}/dev_allRisks_future45.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_allRisks_future.asc.gz ${TARGETFOLDER}/dev_allRisks_future45.asc.gz
sed -i 's/title: .*/title: B/g' ${TARGETFOLDER}/dev_allRisks_future45.asc.meta

# all std
cp ${SOURCEFOLDER}/asciigrid_combined/dev/avg_over_climScen_stdDev.asc.gz ${TARGETFOLDER}/avg_over_climScen_stdDev_future85.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/avg_over_climScen_stdDev.asc.gz ${TARGETFOLDER}/avg_over_climScen_stdDev_future45.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/avg_over_climScen_stdDev.asc.meta ${TARGETFOLDER}/avg_over_climScen_stdDev_future85.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/avg_over_climScen_stdDev.asc.meta ${TARGETFOLDER}/avg_over_climScen_stdDev_future45.asc.meta
sed -i 's/title: .*/title: A/g' ${TARGETFOLDER}/avg_over_climScen_stdDev_future45.asc.meta
sed -i 's/title: .*/title: B/g' ${TARGETFOLDER}/avg_over_climScen_stdDev_future85.asc.meta


cp ${SOURCEFOLDER}/asciigrid_combined/dev/avg_over_models_stdDev.asc.gz ${TARGETFOLDER}/avg_over_models_stdDev_future85.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/avg_over_models_stdDev.asc.gz ${TARGETFOLDER}/avg_over_models_stdDev_future45.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/avg_over_models_stdDev.asc.meta ${TARGETFOLDER}/avg_over_models_stdDev_future85.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/avg_over_models_stdDev.asc.meta ${TARGETFOLDER}/avg_over_models_stdDev_future45.asc.meta
sed -i 's/title: .*/title: B/g' ${TARGETFOLDER}/avg_over_models_stdDev_future45.asc.meta
sed -i 's/title: .*/title: C/g' ${TARGETFOLDER}/avg_over_models_stdDev_future85.asc.meta
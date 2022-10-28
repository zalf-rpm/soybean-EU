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

# average bar chart
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_max_yield_historical.asc.gz ${TARGETFOLDER}/bar_max_yield_historical.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_max_yield_future.asc.gz ${TARGETFOLDER}/bar_max_yield_future45.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_max_yield_future.asc.gz ${TARGETFOLDER}/bar_max_yield_future85.asc.gz
cp ./with_85/bar_max_yield_historical.asc.meta ${TARGETFOLDER}/bar_max_yield_historical.asc.meta
cp ./with_85/bar_max_yield_future45.asc.meta ${TARGETFOLDER}/bar_max_yield_future45.asc.meta
cp ./with_85/bar_max_yield_future85.asc.meta ${TARGETFOLDER}/bar_max_yield_future85.asc.meta
sed -i 's/title: .*/title: a/g' ${TARGETFOLDER}/bar_max_yield_historical.asc.meta
sed -i 's/title: .*/title: b/g' ${TARGETFOLDER}/bar_max_yield_future45.asc.meta
sed -i 's/title: .*/title: c/g' ${TARGETFOLDER}/bar_max_yield_future85.asc.meta

# average yield line chart
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_max_yield_historical.asc.gz ${TARGETFOLDER}/line_max_yield_historical.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_max_yield_future.asc.gz ${TARGETFOLDER}/line_max_yield_future45.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_max_yield_future.asc.gz ${TARGETFOLDER}/line_max_yield_future85.asc.gz
cp ./with_85/line_max_yield_historical.asc.meta ${TARGETFOLDER}/line_max_yield_historical.asc.meta
cp ./with_85/line_max_yield_future45.asc.meta ${TARGETFOLDER}/line_max_yield_future45.asc.meta
cp ./with_85/line_max_yield_future85.asc.meta ${TARGETFOLDER}/line_max_yield_future85.asc.meta

# maturity violin plots
cp ./with_85/violin_maturity_groups_historical.asc.meta ${TARGETFOLDER}/violin_maturity_groups_historical.asc.meta
cp ./with_85/violin_maturity_groups_future85.asc.meta ${TARGETFOLDER}/violin_maturity_groups_future85.asc.meta
cp ./with_85/violin_maturity_groups_future45.asc.meta ${TARGETFOLDER}/violin_maturity_groups_future45.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_historical.asc.gz ${TARGETFOLDER}/violin_maturity_groups_historical.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_future.asc.gz ${TARGETFOLDER}/violin_maturity_groups_future85.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_maturity_groups_future.asc.gz ${TARGETFOLDER}/violin_maturity_groups_future45.asc.gz

#maturity stacked chart
cp ./with_85/stacked_maturity_groups_future45.asc.meta ${TARGETFOLDER}/stacked_maturity_groups_future45.asc.meta
cp ./with_85/stacked_maturity_groups_future85.asc.meta ${TARGETFOLDER}/stacked_maturity_groups_future85.asc.meta
cp ./with_85/stacked_maturity_groups_historical.asc.meta ${TARGETFOLDER}/stacked_maturity_groups_historical.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_historical.asc.gz ${TARGETFOLDER}/stacked_maturity_groups_historical.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_future.asc.gz ${TARGETFOLDER}/stacked_maturity_groups_future85.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_maturity_groups_future.asc.gz ${TARGETFOLDER}/stacked_maturity_groups_future45.asc.gz

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

# share of MG on adaptation
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_share_MG_adaptation_2ed_historical_future.asc.gz ${TARGETFOLDER}/dev_share_MG_adaptation_2ed_historical_future85.asc.gz
cat ${SOURCEFOLDER}/asciigrid_combined/dev/dev_share_MG_adaptation_2ed_historical_future.asc.meta ./with_85/yLabel_latidude.meta > ${TARGETFOLDER}/dev_share_MG_adaptation_2ed_historical_future85.asc.meta

cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_share_MG_adaptation_2ed_historical_future.asc.gz ${TARGETFOLDER}/dev_share_MG_adaptation_2ed_historical_future45.asc.gz
cat ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_share_MG_adaptation_2ed_historical_future.asc.meta  ./with_85/yLabel_latidude.meta > ${TARGETFOLDER}/dev_share_MG_adaptation_2ed_historical_future45.asc.meta


sed -i 's/title: .*/title: a/g' ${TARGETFOLDER}/dev_share_MG_adaptation_2ed_historical_future45.asc.meta
sed -i 's/title: .*/title: b/g' ${TARGETFOLDER}/dev_share_MG_adaptation_2ed_historical_future85.asc.meta
sed -i 's/colormap: .*/colormap: gnuplot/g'  ${TARGETFOLDER}/dev_share_MG_adaptation_2ed_historical_future45.asc.meta
sed -i 's/colormap: .*/colormap: gnuplot/g' ${TARGETFOLDER}/dev_share_MG_adaptation_2ed_historical_future85.asc.meta

MAXVALUE=$( ../sync_versions/sync_versions.exe -source1 ${TARGETFOLDER}/dev_share_MG_adaptation_2ed_historical_future45.asc.meta -source2 ${TARGETFOLDER}/dev_share_MG_adaptation_2ed_historical_future85.asc.meta)
sed -i "s/maxValue: .*/maxValue: ${MAXVALUE}/g"  ${TARGETFOLDER}/dev_share_MG_adaptation_2ed_historical_future45.asc.meta
sed -i "s/maxValue: .*/maxValue: ${MAXVALUE}/g" ${TARGETFOLDER}/dev_share_MG_adaptation_2ed_historical_future85.asc.meta


#Sowing dates

cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_sowing_historical.asc.gz ${TARGETFOLDER}/dev_sowing_historical.asc.gz
cat ${SOURCEFOLDER}/asciigrid_combined/dev/dev_sowing_historical.asc.meta ./with_85/yLabel_latidude.meta > ${TARGETFOLDER}/dev_sowing_historical.asc.meta
sed -i 's/title: .*/title: a/g' ${TARGETFOLDER}/dev_sowing_historical.asc.meta

cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_sowing_future.asc.gz ${TARGETFOLDER}/dev_sowing_future45.asc.gz
cat ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_sowing_future.asc.meta  ./with_85/yLabel_latidude.meta > ${TARGETFOLDER}/dev_sowing_future45.asc.meta
sed -i 's/title: .*/title: b/g' ${TARGETFOLDER}/dev_sowing_future45.asc.meta

cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_sowing_future.asc.gz ${TARGETFOLDER}/dev_sowing_future85.asc.gz
cat ${SOURCEFOLDER}/asciigrid_combined/dev/dev_sowing_future.asc.meta ./with_85/yLabel_latidude.meta > ${TARGETFOLDER}/dev_sowing_future85.asc.meta
sed -i 's/title: .*/title: c/g' ${TARGETFOLDER}/dev_sowing_future85.asc.meta



# irrigation map
cp ${SOURCEFOLDER}/asciigrid_combined/dev/irrgated_areas.asc.meta ${TARGETFOLDER}/irrgated_areas.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/irrgated_areas.asc.gz ${TARGETFOLDER}/irrgated_areas.asc.gz
# all yield heatmap
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_max_yield_historical.asc.meta ${TARGETFOLDER}/dev_max_yield_historical.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_max_yield_historical.asc.gz ${TARGETFOLDER}/dev_max_yield_historical.asc.gz
sed -i 's/title: .*/title: a/g' ${TARGETFOLDER}/dev_max_yield_historical.asc.meta

cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_max_yield_future.asc.meta ${TARGETFOLDER}/dev_max_yield_future85.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_max_yield_future.asc.gz ${TARGETFOLDER}/dev_max_yield_future85.asc.gz
sed -i 's/title: .*/title: c/g' ${TARGETFOLDER}/dev_max_yield_future85.asc.meta

cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_max_yield_future.asc.meta ${TARGETFOLDER}/dev_max_yield_future45.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_max_yield_future.asc.gz ${TARGETFOLDER}/dev_max_yield_future45.asc.gz
sed -i 's/title: .*/title: b/g' ${TARGETFOLDER}/dev_max_yield_future45.asc.meta

# all maturity group heatmaps
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_historical.asc.meta ${TARGETFOLDER}/dev_maturity_groups_historical.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_historical.asc.gz ${TARGETFOLDER}/dev_maturity_groups_historical.asc.gz
sed -i 's/title: .*/title: a/g' ${TARGETFOLDER}/dev_maturity_groups_historical.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_future.asc.meta ${TARGETFOLDER}/dev_maturity_groups_future85.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_future.asc.gz ${TARGETFOLDER}/dev_maturity_groups_future85.asc.gz
sed -i 's/title: .*/title: c/g' ${TARGETFOLDER}/dev_maturity_groups_future85.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_maturity_groups_future.asc.meta ${TARGETFOLDER}/dev_maturity_groups_future45.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_maturity_groups_future.asc.gz ${TARGETFOLDER}/dev_maturity_groups_future45.asc.gz
sed -i 's/title: .*/title: b/g' ${TARGETFOLDER}/dev_maturity_groups_future45.asc.meta
# all risk heatmaps
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_allRisks_historical.asc.meta ${TARGETFOLDER}/dev_allRisks_historical.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_allRisks_historical.asc.gz ${TARGETFOLDER}/dev_allRisks_historical.asc.gz
sed -i 's/title: .*/title: a/g' ${TARGETFOLDER}/dev_allRisks_historical.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_allRisks_future.asc.meta ${TARGETFOLDER}/dev_allRisks_future85.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_allRisks_future.asc.gz ${TARGETFOLDER}/dev_allRisks_future85.asc.gz
sed -i 's/title: .*/title: c/g' ${TARGETFOLDER}/dev_allRisks_future85.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_allRisks_future.asc.meta ${TARGETFOLDER}/dev_allRisks_future45.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_allRisks_future.asc.gz ${TARGETFOLDER}/dev_allRisks_future45.asc.gz
sed -i 's/title: .*/title: b/g' ${TARGETFOLDER}/dev_allRisks_future45.asc.meta

# all risk heatmaps with 5 risks
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_allRisks_5_historical.asc.meta ${TARGETFOLDER}/dev_allRisks_5_historical.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_allRisks_5_historical.asc.gz ${TARGETFOLDER}/dev_allRisks_5_historical.asc.gz
sed -i 's/title: .*/title: a/g' ${TARGETFOLDER}/dev_allRisks_5_historical.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_allRisks_5_future.asc.meta ${TARGETFOLDER}/dev_allRisks_5_future85.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_allRisks_5_future.asc.gz ${TARGETFOLDER}/dev_allRisks_5_future85.asc.gz
sed -i 's/title: .*/title: c/g' ${TARGETFOLDER}/dev_allRisks_5_future85.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_allRisks_5_future.asc.meta ${TARGETFOLDER}/dev_allRisks_5_future45.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_allRisks_5_future.asc.gz ${TARGETFOLDER}/dev_allRisks_5_future45.asc.gz
sed -i 's/title: .*/title: b/g' ${TARGETFOLDER}/dev_allRisks_5_future45.asc.meta

# all std
cp ${SOURCEFOLDER}/asciigrid_combined/dev/avg_over_climScen_stdDev.asc.gz ${TARGETFOLDER}/avg_over_climScen_stdDev_future85.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/avg_over_climScen_stdDev.asc.gz ${TARGETFOLDER}/avg_over_climScen_stdDev_future45.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/avg_over_climScen_stdDev.asc.meta ${TARGETFOLDER}/avg_over_climScen_stdDev_future85.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/avg_over_climScen_stdDev.asc.meta ${TARGETFOLDER}/avg_over_climScen_stdDev_future45.asc.meta
sed -i 's/title: .*/title: c/g' ${TARGETFOLDER}/avg_over_climScen_stdDev_future45.asc.meta
sed -i 's/title: .*/title: c/g' ${TARGETFOLDER}/avg_over_climScen_stdDev_future85.asc.meta


cp ${SOURCEFOLDER}/asciigrid_combined/dev/avg_over_models_stdDev.asc.gz ${TARGETFOLDER}/avg_over_models_stdDev_future85.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/avg_over_models_stdDev.asc.gz ${TARGETFOLDER}/avg_over_models_stdDev_future45.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/avg_over_models_stdDev.asc.meta ${TARGETFOLDER}/avg_over_models_stdDev_future85.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/avg_over_models_stdDev.asc.meta ${TARGETFOLDER}/avg_over_models_stdDev_future45.asc.meta
sed -i 's/title: .*/title: b/g' ${TARGETFOLDER}/avg_over_models_stdDev_future45.asc.meta
sed -i 's/title: .*/title: b/g' ${TARGETFOLDER}/avg_over_models_stdDev_future85.asc.meta

sed -i 's/yellow/cyan/g' ${TARGETFOLDER}/avg_over_models_stdDev_future45.asc.meta
sed -i 's/yellow/cyan/g' ${TARGETFOLDER}/avg_over_models_stdDev_future85.asc.meta
sed -i 's/orange/violet/g' ${TARGETFOLDER}/avg_over_models_stdDev_future45.asc.meta
sed -i 's/orange/violet/g' ${TARGETFOLDER}/avg_over_models_stdDev_future85.asc.meta

# cp ${SOURCEFOLDER}/asciigrid_combined/dev/all_historical_stdDev.asc.gz ${TARGETFOLDER}/all_historical_stdDev.asc.gz
# cp ${SOURCEFOLDER}/asciigrid_combined/dev/all_historical_stdDev.asc.meta ${TARGETFOLDER}/all_historical_stdDev.asc.meta
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/all_future_stdDev.asc.gz ${TARGETFOLDER}/all_future_stdDev45.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/all_future_stdDev.asc.meta ${TARGETFOLDER}/all_future_stdDev45.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/all_future_stdDev.asc.gz ${TARGETFOLDER}/all_future_stdDev85.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/all_future_stdDev.asc.meta ${TARGETFOLDER}/all_future_stdDev85.asc.meta
# sed -i 's/title: .*/title: A/g' ${TARGETFOLDER}/all_historical_stdDev.asc.meta
sed -i 's/title: .*/title: a/g' ${TARGETFOLDER}/all_future_stdDev45.asc.meta
sed -i 's/title: .*/title: a/g' ${TARGETFOLDER}/all_future_stdDev85.asc.meta

sed -i 's/pink/cyan/g' ${TARGETFOLDER}/all_future_stdDev45.asc.meta
sed -i 's/pink/cyan/g' ${TARGETFOLDER}/all_future_stdDev85.asc.meta
sed -i 's/orangered/violet/g' ${TARGETFOLDER}/all_future_stdDev45.asc.meta
sed -i 's/orangered/violet/g' ${TARGETFOLDER}/all_future_stdDev85.asc.meta


# density plots
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_drought_risk_historical.asc.gz ${TARGETFOLDER}/density_drought_risk_historical.asc.gz 
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_drought_risk_future.asc.gz ${TARGETFOLDER}/density_drought_risk_future45.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_drought_risk_future.asc.gz ${TARGETFOLDER}/density_drought_risk_future85.asc.gz 
cp ./with_85/density_drought_risk_historical.asc.meta ${TARGETFOLDER}/density_drought_risk_historical.asc.meta
cp ./with_85/density_drought_risk_future45.asc.meta ${TARGETFOLDER}/density_drought_risk_future45.asc.meta
cp ./with_85/density_drought_risk_future85.asc.meta ${TARGETFOLDER}/density_drought_risk_future85.asc.meta

cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_short_season_historical.asc.gz ${TARGETFOLDER}/density_short_season_historical.asc.gz 
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_short_season_future.asc.gz ${TARGETFOLDER}/density_short_season_future45.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_short_season_future.asc.gz ${TARGETFOLDER}/density_short_season_future85.asc.gz 
cp ./with_85/density_short_season_historical.asc.meta ${TARGETFOLDER}/density_short_season_historical.asc.meta
cp ./with_85/density_short_season_future45.asc.meta ${TARGETFOLDER}/density_short_season_future45.asc.meta
cp ./with_85/density_short_season_future85.asc.meta ${TARGETFOLDER}/density_short_season_future85.asc.meta

cp ${SOURCEFOLDER}/asciigrid_combined/dev/coldSpell_historical.asc.gz ${TARGETFOLDER}/density_coldSpell_historical.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/coldSpell_future.asc.gz ${TARGETFOLDER}/density_coldSpell_future45.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/coldSpell_future.asc.gz ${TARGETFOLDER}/density_coldSpell_future85.asc.gz
cp ./with_85/density_coldSpell_future45.asc.meta ${TARGETFOLDER}/density_coldSpell_future45.asc.meta
cp ./with_85/density_coldSpell_future85.asc.meta ${TARGETFOLDER}/density_coldSpell_future85.asc.meta
cp ./with_85/density_coldSpell_historical.asc.meta ${TARGETFOLDER}/density_coldSpell_historical.asc.meta

cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_harvest_rain_historical.asc.gz ${TARGETFOLDER}/density_harvest_rain_historical.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_harvest_rain_future.asc.gz ${TARGETFOLDER}/density_harvest_rain_future45.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_harvest_rain_future.asc.gz ${TARGETFOLDER}/density_harvest_rain_future85.asc.gz
cp ./with_85/density_harvest_rain_future45.asc.meta ${TARGETFOLDER}/density_harvest_rain_future45.asc.meta
cp ./with_85/density_harvest_rain_future85.asc.meta ${TARGETFOLDER}/density_harvest_rain_future85.asc.meta
cp ./with_85/density_harvest_rain_historical.asc.meta ${TARGETFOLDER}/density_harvest_rain_historical.asc.meta

# maturity violin plots
cp ./with_85/violin_maturity_groups_historical.asc.meta ${TARGETFOLDER}/one_violin_maturity_groups_historical.asc.meta
cp ./with_85/violin_maturity_groups_future85.asc.meta ${TARGETFOLDER}/one_violin_maturity_groups_future85.asc.meta
cp ./with_85/violin_maturity_groups_future45.asc.meta ${TARGETFOLDER}/one_violin_maturity_groups_future45.asc.meta
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_historical.asc.gz ${TARGETFOLDER}/one_violin_maturity_groups_historical.asc.gz
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_maturity_groups_future.asc.gz ${TARGETFOLDER}/one_violin_maturity_groups_future85.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_maturity_groups_future.asc.gz ${TARGETFOLDER}/one_violin_maturity_groups_future45.asc.gz
# risk violin plots
# risk cold spell 
cp ${SOURCEFOLDER}/asciigrid_combined/dev/coldSpell_historical.asc.gz ${TARGETFOLDER}/one_violin_coldSpell_historical.asc.gz 
cp ${SOURCEFOLDER}/asciigrid_combined/dev/coldSpell_future.asc.gz ${TARGETFOLDER}/one_violin_coldSpell_future85.asc.gz 
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/coldSpell_future.asc.gz ${TARGETFOLDER}/one_violin_coldSpell_future45.asc.gz
cp ./with_85/violin_coldSpell_historical.asc.meta ${TARGETFOLDER}/one_violin_coldSpell_historical.asc.meta
cp ./with_85/violin_coldSpell_future85.asc.meta ${TARGETFOLDER}/one_violin_coldSpell_future85.asc.meta
cp ./with_85/violin_coldSpell_future45.asc.meta ${TARGETFOLDER}/one_violin_coldSpell_future45.asc.meta
# risk drought
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_drought_risk_historical.asc.gz ${TARGETFOLDER}/one_violin_drought_risk_historical.asc.gz 
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_drought_risk_future.asc.gz ${TARGETFOLDER}/one_violin_drought_risk_future85.asc.gz 
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_drought_risk_future.asc.gz ${TARGETFOLDER}/one_violin_drought_risk_future45.asc.gz
cp ./with_85/violin_drought_risk_historical.asc.meta ${TARGETFOLDER}/one_violin_drought_risk_historical.asc.meta
cp ./with_85/violin_drought_risk_future85.asc.meta ${TARGETFOLDER}/one_violin_drought_risk_future85.asc.meta
cp ./with_85/violin_drought_risk_future45.asc.meta ${TARGETFOLDER}/one_violin_drought_risk_future45.asc.meta
# risk harvest rain 
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_harvest_rain_historical.asc.gz ${TARGETFOLDER}/one_violin_harvest_rain_historical.asc.gz 
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_harvest_rain_future.asc.gz ${TARGETFOLDER}/one_violin_harvest_rain_future85.asc.gz 
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_harvest_rain_future.asc.gz ${TARGETFOLDER}/one_violin_harvest_rain_future45.asc.gz
cp ./with_85/violin_harvest_rain_historical.asc.meta ${TARGETFOLDER}/one_violin_harvest_rain_historical.asc.meta
cp ./with_85/violin_harvest_rain_future85.asc.meta ${TARGETFOLDER}/one_violin_harvest_rain_future85.asc.meta
cp ./with_85/violin_harvest_rain_future45.asc.meta ${TARGETFOLDER}/one_violin_harvest_rain_future45.asc.meta
# risk short season
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_short_season_historical.asc.gz ${TARGETFOLDER}/one_violin_short_season_historical.asc.gz 
cp ${SOURCEFOLDER}/asciigrid_combined/dev/dev_short_season_future.asc.gz ${TARGETFOLDER}/one_violin_short_season_future85.asc.gz
cp ${SOURCEFOLDER45}/asciigrid_combined/dev/dev_short_season_future.asc.gz ${TARGETFOLDER}/one_violin_short_season_future45.asc.gz
cp ./with_85/violin_short_season_historical.asc.meta ${TARGETFOLDER}/one_violin_short_season_historical.asc.meta
cp ./with_85/one_violin_short_season_future85.asc.meta ${TARGETFOLDER}/one_violin_short_season_future85.asc.meta
cp ./with_85/violin_short_season_future45.asc.meta ${TARGETFOLDER}/one_violin_short_season_future45.asc.meta

sed -i 's/violinOffset: .*/violinOffset: 48/g' ${TARGETFOLDER}/one_violin_coldSpell_historical.asc.meta
sed -i 's/violinOffset: .*/violinOffset: 50/g' ${TARGETFOLDER}/one_violin_coldSpell_future45.asc.meta
sed -i 's/violinOffset: .*/violinOffset: 52/g' ${TARGETFOLDER}/one_violin_coldSpell_future85.asc.meta
sed -i 's/violinOffset: .*/violinOffset: 54/g' ${TARGETFOLDER}/one_violin_drought_risk_historical.asc.meta
sed -i 's/violinOffset: .*/violinOffset: 56/g' ${TARGETFOLDER}/one_violin_drought_risk_future45.asc.meta
sed -i 's/violinOffset: .*/violinOffset: 58/g' ${TARGETFOLDER}/one_violin_drought_risk_future85.asc.meta
sed -i 's/violinOffset: .*/violinOffset: 60/g' ${TARGETFOLDER}/one_violin_harvest_rain_historical.asc.meta
sed -i 's/violinOffset: .*/violinOffset: 62/g' ${TARGETFOLDER}/one_violin_harvest_rain_future45.asc.meta
sed -i 's/violinOffset: .*/violinOffset: 64/g' ${TARGETFOLDER}/one_violin_harvest_rain_future85.asc.meta
sed -i 's/violinOffset: .*/violinOffset: 66/g' ${TARGETFOLDER}/one_violin_short_season_historical.asc.meta
sed -i 's/violinOffset: .*/violinOffset: 68/g' ${TARGETFOLDER}/one_violin_short_season_future45.asc.meta
sed -i 's/violinOffset: .*/violinOffset: 70/g' ${TARGETFOLDER}/one_violin_short_season_future85.asc.meta
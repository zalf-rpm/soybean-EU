#!/bin/bash -x
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --partition=compute
#SBATCH --job-name=img_gen_ascii
#SBATCH --time=4:00:00 

FOLDER=$( pwd )
IMG=~/singularity/python/python3.7_2.0.sif
singularity run -B $FOLDER/asciigrid:/source,$FOLDER:/out $IMG python create_image_from_ascii.py path=cluster
#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=4GB
#SBATCH --partition=braintv
#SBATCH --time=24:00:00
source ~/miniconda3/etc/profile.d/conda.sh
conda activate /allen/programs/mindscope/workgroups/openscope/environment/nextflow
cd /home/jeromel/nextflow
./nextflow deepinterpolation.nf

#!/bin/bash -l

#$ -N tune_vqvae_test
#$ -P textconv
#$ -o tune_vqvae_test
#$ -pe omp 8
#$ -l gpus=1 
#$ -l gpu_c=6 
#$ -m ea
 
module load miniconda/4.7.5
conda activate pytorch-1.3.1-lms
export PYTHONPATH=/projectnb/textconv/ykh/jukebox:$PYTHONPATH

python jukebox/train.py --hps=vqvae,small_labelled_prior,all_fp16,cpu_ema --name=pretrained_vqvae_small_prior --sample_length=1048576 --bs=4 --audio_files_dir=/projectnb/textconv/jukebox/dataset/test --labels=True --labels_v3=True --train --test --aug_shift --aug_blend --restore_vqvae=/projectnb/textconv/jukebox/jukebox/download/jukebox-assets/models/5b/vqvae.pth.tar --prior --levels=3 --level=2 --weight_decay=0.01 --save_iters=1000 --audio_database=/projectnb/textconv/jukebox/dataset/database.csv

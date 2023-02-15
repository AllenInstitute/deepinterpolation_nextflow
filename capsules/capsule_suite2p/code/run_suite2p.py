import argparse
import os
import glob
import sys 
import datetime
import suite2p
import shutil
import numpy as np 

data_folder = "../data/"
results_folder = "../results/"
scratch_folder = "../results/"

if __name__ == "__main__":
    print(argparse.__version__)
    print(sys.argv)

    parser = argparse.ArgumentParser()
    parser.add_argument("--sampling_rate", type=float, default=30)
    parser.add_argument("--suite2p_threshold_scaling", type=float, default=1)
    parser.add_argument("--copy_input_file_scratch", default=False, action="store_true")
    parser.add_argument("--input_movie_path", type=str, default='../data/allen-test-2p/6f9947f4-1fa3-4ea4-a29b-46223ce972db')

    args = parser.parse_args()
    
    print("Preparing data for fine-tuning")

    sampling_rate = args.sampling_rate
    suite2p_threshold_scaling = args.suite2p_threshold_scaling
    copy_input_file_scratch = args.copy_input_file_scratch
    s3_file = args.input_movie_path
    
    if copy_input_file_scratch: 
        input_movie_s3 = s3_file
        input_movie_path = scratch_folder+'ophys_experiment.h5'
    
        print("Copying S3 file locally")
        shutil.copy(input_movie_s3, input_movie_path, follow_symlinks=True)
        print("Done copying S3 file locally")
    else:
        input_movie_path = s3_file

    ops = suite2p.default_ops()
    ops['threshold_scaling'] = suite2p_threshold_scaling 
    ops['fs'] = float(sampling_rate) # sampling rate of recording, determines binning for cell detection
    ops['tau'] = 1 # timescale of gcamp to use for deconvolution
    ops['do_registration'] = 0 # data was already registered
    ops['save_NWB'] = 1
    ops['save_folder'] = results_folder
    ops['fast_disk'] = scratch_folder

    db = {
    'h5py': input_movie_path,
    'data_path': []
    }

    output_ops = suite2p.run_s2p(ops=ops, db=db)
    
    shutil.rmtree(os.path.join(results_folder, 'suite2p', 'plane0'))


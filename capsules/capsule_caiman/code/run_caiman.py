import bokeh.plotting as bpl
import glob
import logging
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import shutil
import argparse
import caiman as cm
from caiman.motion_correction import MotionCorrect
from caiman.source_extraction.cnmf import cnmf as cnmf
from caiman.source_extraction.cnmf import params as params
from caiman.utils.utils import download_demo
from caiman.utils.visualization import plot_contours, nb_view_patches, nb_plot_contour
bpl.output_notebook()
import cv2

try:
    cv2.setNumThreads(1)
except:
    print('Open CV is naturally single threaded')

data_folder = "../data/"
results_folder = "../results/"
scratch_folder = "../results/"

logging.basicConfig(format=
                          "%(relativeCreated)12d [%(filename)s:%(funcName)20s():%(lineno)s] [%(process)d] %(message)s",
                    # filename="/tmp/caiman.log",
                    level=logging.WARNING)

if __name__ == "__main__":
    print(argparse.__version__)
    print(sys.argv)

    parser = argparse.ArgumentParser()
    parser.add_argument("--sampling_rate", type=float, default=30)
    parser.add_argument("--copy_input_file_scratch", default=True, action="store_true")
    parser.add_argument("--input_movie_path", type=str, default='../data/allen-test-2p/6f9947f4-1fa3-4ea4-a29b-46223ce972db')

    args = parser.parse_args()
    
    print("Preparing data for fine-tuning")

    sampling_rate = args.sampling_rate
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

    fnames = [input_movie_path]  # filename to be processed

    # dataset dependent parameters
    fr = sampling_rate                            # imaging rate in frames per second
    decay_time = 0.4                    # length of a typical transient in seconds

    # motion correction parameters
    strides = (48, 48)          # start a new patch for pw-rigid motion correction every x pixels
    overlaps = (24, 24)         # overlap between pathes (size of patch strides+overlaps)
    max_shifts = (6,6)          # maximum allowed rigid shifts (in pixels)
    max_deviation_rigid = 3     # maximum shifts deviation allowed for patch with respect to rigid shifts
    pw_rigid = False             # flag for performing non-rigid motion correction

    # parameters for source extraction and deconvolution
    p = 1                       # order of the autoregressive system
    gnb = 2                     # number of global background components
    merge_thr = 0.85            # merging threshold, max correlation allowed
    rf = 15                     # half-size of the patches in pixels. e.g., if rf=25, patches are 50x50
    stride_cnmf = 6             # amount of overlap between the patches in pixels
    K = 4                       # number of components per patch
    gSig = [4, 4]               # expected half size of neurons in pixels
    method_init = 'greedy_roi'  # initialization method (if analyzing dendritic data using 'sparse_nmf')
    ssub = 1                    # spatial subsampling during initialization
    tsub = 1                    # temporal subsampling during intialization

    # parameters for component evaluation
    min_SNR = 2.0               # signal to noise ratio for accepting a component
    rval_thr = 0.85              # space correlation threshold for accepting a component
    cnn_thr = 0.99              # threshold for CNN based classifier
    cnn_lowest = 0.1 # neurons with cnn probability lower than this value are rejected

    opts_dict = {'fnames': fnames,
                'fr': fr,
                'decay_time': decay_time,
                'strides': strides,
                'overlaps': overlaps,
                'max_shifts': max_shifts,
                'max_deviation_rigid': max_deviation_rigid,
                'pw_rigid': pw_rigid,
                'p': p,
                'nb': gnb,
                'rf': rf,
                'K': K, 
                'gSig': gSig,
                'stride': stride_cnmf,
                'method_init': method_init,
                'rolling_sum': True,
                'only_init': True,
                'ssub': ssub,
                'tsub': tsub,
                'merge_thr': merge_thr, 
                'min_SNR': min_SNR,
                'rval_thr': rval_thr,
                'use_cnn': True,
                'min_cnn_thr': cnn_thr,
                'cnn_lowest': cnn_lowest}

    opts = params.CNMFParams(params_dict=opts_dict)

    c, dview, n_processes = cm.cluster.setup_cluster(backend='local', n_processes=None, single_thread=False)

    #%% RUN CNMF ON PATCHES
    # First extract spatial and temporal components on patches and combine them
    # for this step deconvolution is turned off (p=0). If you want to have
    # deconvolution within each patch change params.patch['p_patch'] to a
    # nonzero value
    cnm = cnmf.CNMF(n_processes, params=opts, dview=dview)
    cnm.fit_file(motion_correct=False)
    cnm.save(os.path.join(results_folder, 'analysis_results.hdf5'))
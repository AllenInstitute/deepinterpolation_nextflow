import argparse
import os
from deepinterpolation.cli.fine_tuning import FineTuning
from deepinterpolation.cli.inference import Inference
import glob
import sys 
import datetime
import shutil
import h5py 
import json
from pathlib import Path
import uuid
import numpy as np 

data_folder = "../data/"
results_folder = "../results/"
scratch_folder = "../results/"

if __name__ == "__main__":
    print(argparse.__version__)
    print(sys.argv)

    parser = argparse.ArgumentParser()
    
    parser.add_argument("--input_frame_range", type=str, default='../data/List_of_frames_intervals/movie_param0.json')

    parser.add_argument("--nb_workers", type=int, default=10)

    parser.add_argument("--copy_input_file_scratch", default=False, action="store_true")
    parser.add_argument("--cache_input_data", default=False, action="store_true")
    parser.add_argument("--input_movie_path", type=str, default='../data/allen-test-2p/6f9947f4-1fa3-4ea4-a29b-46223ce972db')
    parser.add_argument("--inference_model_path", type=str, default='../data/DeepInterpolation_2p_models/2021_07_31_09_49_38_095550_unet_1024_search_mean_squared_error_pre_30_post_30_feat_32_power_1_depth_4_unet_True-0125-0.5732.h5')

    parser.add_argument("--pre_frame", type=int, default=30)
    parser.add_argument("--post_frame", type=int, default=30)
    parser.add_argument("--pre_post_omission", type=int, default=0)

    args = parser.parse_args()
    input_movie_path = args.input_movie_path

    input_frame_range = args.input_frame_range

    pre_frame = args.pre_frame
    post_frame = args.post_frame
    pre_post_omission = args.pre_post_omission

    #list_range_files =  glob.glob(os.path.join(input_frame_range, "*.json"))
    #print(list_range_files)
    #first_file = list_range_files[0]

    with open(input_frame_range) as file_handle:
        try:
            data = json.load(file_handle)
            frame_start = data['start']
            frame_end = data['end']

            if frame_start == frame_end:
                data = {}
                Path(os.path.join(results_folder, str(uuid.uuid4()))).touch()
        except: 
            data = {}
            # Code ocean would crash if no file output in pipeline mode
            # So here we go
            Path(os.path.join(results_folder, str(uuid.uuid4()))).touch()

    if (len(data) == 0):
        print("start and end frame missing in json input file")
    else:
        nb_workers = args.nb_workers

        copy_input_file_scratch = args.copy_input_file_scratch
        cache_input_data = args.cache_input_data
        inference_model_path = args.inference_model_path

        print("nb_frame_inference :"+str(frame_end-frame_start))

        with h5py.File(input_movie_path, 'r') as file_handle:
            movie_size = file_handle['data'].shape
            print("Original movie has "+str(movie_size[0])+" frame(s).")
            print("target frame range is from frame "+str(frame_start)+" to "+str(frame_end))

            # This is to handle negative frame_end parameters
            if frame_end < 0:
                old_frame_end = frame_end
                frame_end = movie_size[0] + frame_end
                print("Negative frame target "+str(old_frame_end)+" converted to " +frame_end)

            # This is to handle end_frame beyond the current end of the movie
            if frame_end > movie_size[0] - 1 - post_frame - pre_post_omission:
                old_frame_end = frame_end
                frame_end = movie_size[0] - 1 - post_frame - pre_post_omission
                print("Frame target "+str(old_frame_end)+" exceeded movie size of "+str(movie_size[0])+", converted to " +str(frame_end))
                
            if frame_start < movie_size[0]:
                local_frame_start = frame_start
                local_frame_end = frame_end
                if copy_input_file_scratch: 
                    movie_path = scratch_folder+'input_ophys_experiment.h5'
                    file_handle['data']
                    # We copy the whole file or section of it depending on the range asked
                    if frame_end-frame_start>5000:
                        if not os.path.isfile(movie_path):
                            print("Copying S3 file locally")
                            shutil.copy(input_movie_path, movie_path)
                            print("Done copying S3 file locally")
                    else: 
                        # this part is key to avoid black gaps due to padding.
                        pre_offset = np.min([frame_start, pre_frame + pre_post_omission])
                        post_offset = np.min([movie_size[0]-1-frame_end, post_frame + pre_post_omission])

                        local_frame_start = pre_offset
                        local_frame_end = pre_offset + frame_end - frame_start

                        print("Adjusting global frames: "+str(frame_start)+" - "+str(frame_end)+ " to local frames: "+str(local_frame_start)+" - "+str(local_frame_end))

                        with h5py.File(movie_path, 'w') as h5_out_handle:
                            local_data = file_handle['data'][(frame_start- pre_offset):(frame_end+post_offset+1), :, :]
                            chunk_size = list(movie_size)
                            chunk_size[0] = 1
                            h5_out_handle.create_dataset('data', data=local_data, chunks=tuple(chunk_size))
                            # clean up memory
                            del(local_data)
                else:
                    movie_path = input_movie_path


        # This is to handle frame_start beyond the end of the movie. 
        if frame_start>=movie_size[0]:
            print("No frames available for inference at these indices")
            Path(os.path.join(results_folder, str(uuid.uuid4()))).touch()
        else:
            print("Preparing data for inference")
            
            # Initialize meta-parameters objects
            inference_param = {}

            # Initialize meta-parameters objects
            generator_param = {}

            # Those are parameters used for the Validation test generator.
            # Here the test is done on the beginning of the data but
            # this can be a separate file
            generator_param["name"] = "OphysGenerator"  # Name of object
            # in the collection
            generator_param["pre_frame"] = pre_frame
            generator_param["post_frame"] = post_frame
            generator_param["data_path"] = movie_path
            generator_param["start_frame"] = local_frame_start
            generator_param["end_frame"] = local_frame_end
            generator_param["pre_post_omission"] = pre_post_omission  # Number of frame omitted before and after the predicted frame
            generator_param["cache_data"] = cache_input_data
            generator_param["batch_size"] = 1 # inference needs to be done in batch of one to guarantee no lost frames in the end and avoid unfilled batches.

            # This is the name of the underlying inference class called
            inference_param["name"] = "core_inferrence"

            # Replace this path to where you stored your model
            inference_param["use_multiprocessing"] = True
            inference_param["nb_workers"] = nb_workers
            inference_param["steps_per_epoch"] = 50    
            inference_param["model_source"] = {
                "local_path": inference_model_path
            }

            base_file = os.path.splitext(os.path.basename(input_movie_path))[0]
                    
            unique_time = str(datetime.datetime.now()).replace(".","-").replace(":","-").replace(" ","-")

            # Replace this path to where you want to store your output file
            inference_param[
            "output_file"
            ] = os.path.join(results_folder, 'ophys-movie-denoised-from-'+format(frame_start, '07d')+'-to-'+format(frame_end, '07d')+'.h5')
                
            # This option is to add blank frames at the onset and end of the output
            # movie if some output frames are missing input frames to go through
            # the model. This could be present at the start and end of the movie.
            inference_param["output_padding"] = False

            # this is an optional parameter to bring back output data to a given
            # precision. Read the CLI documentation for more details.
            # this is available through
            # 'python -m deepinterpolation.cli.inference --help'
            inference_param["output_datatype"] = 'uint16'

            args = {
                "generator_params": generator_param,
                "inference_params": inference_param,
                "output_full_args": True
            }

            inference_obj = Inference(input_data=args, args=[])
                
            print("Starting inference from local frame:"+str(local_frame_start)+" to frame: "+str(local_frame_end))
            inference_obj.run()
            print("Inference finished")

            del(inference_obj)

            # We delete output json file to avoid overlaps when merging
            [os.remove(f) for f in glob.glob(os.path.join(results_folder, '*.json'))]           
            if copy_input_file_scratch: 
                os.remove(movie_path)

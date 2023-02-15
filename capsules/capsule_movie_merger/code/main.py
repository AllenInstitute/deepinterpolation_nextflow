import argparse
import os
import glob
import sys 
import shutil
import h5py 
import numpy as np

results_folder = "../results/"
data_folder = "../data/"

if __name__ == "__main__":
    # This is just template parameter input, to replace if needed
    parser = argparse.ArgumentParser()
    parser.add_argument("--no_param", type=int, default=0)
 
    args = parser.parse_args()
    no_param = args.no_param

    all_movies = glob.glob(os.path.join(data_folder, "**/ophys-movie-denoised-from-*.h5"))
    output_type = 'uint16'

    if len(all_movies)>0:
        # we sort to ensure order
        all_movies = np.sort(all_movies)
    
        # We merge the files
        output_merged = os.path.join(results_folder, "merged_movie.h5" )

        nb_frames = 0
        for each_file in all_movies:
            with h5py.File(each_file, "r") as file_handle:
                local_shape = file_handle["data"].shape
                nb_frames = nb_frames + local_shape[0]

        final_shape = list(local_shape)
        final_shape[0] = nb_frames

        global_index_frame = 0
        with h5py.File(output_merged, "w") as file_handle:
            dset_out = file_handle.create_dataset(
                "data",
                shape=final_shape,
                chunks=(1, final_shape[1], final_shape[2]),
                dtype=output_type,
            )

            for each_file in all_movies:
                print("Merging "+each_file)
                with h5py.File(each_file, "r") as file_handle:
                    local_shape = file_handle["data"].shape
                    dset_out[
                        global_index_frame : global_index_frame + local_shape[0], :, :
                    ] = file_handle["data"][:, :, :].astype(output_type)
                    global_index_frame += local_shape[0]
    else:
        print("No file to merge")

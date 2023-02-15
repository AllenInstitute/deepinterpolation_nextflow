import argparse
import os
from deepinterpolation.cli.fine_tuning import FineTuning
from deepinterpolation.cli.inference import Inference
import glob
import sys 
import shutil

data_folder = "../data/"
results_folder = "../results/"
scratch_folder = "../results/"

if __name__ == "__main__":
    print(argparse.__version__)
    print(sys.argv)

    parser = argparse.ArgumentParser()
    parser.add_argument("--nb_frame_training", type=int, default=1000)
    parser.add_argument("--copy_input_file_scratch", default=False, action="store_true")
    parser.add_argument("--keep_input_movie_in_output", default=False, action="store_true")
    parser.add_argument("--input_movie_path", type=str, default='../data/allen-test-2p/6f9947f4-1fa3-4ea4-a29b-46223ce972db')
    parser.add_argument("--input_model_path", type=str, default='../data/DeepInterpolation_2p_models/2021_07_31_09_49_38_095550_unet_1024_search_mean_squared_error_pre_30_post_30_feat_32_power_1_depth_4_unet_True-0125-0.5732.h5')

    args = parser.parse_args()
    
    print("Preparing data for fine-tuning")

    nb_frame_training = args.nb_frame_training
    copy_input_file_scratch = args.copy_input_file_scratch
    input_movie_path = args.input_movie_path
    input_model_path = args.input_model_path
    keep_input_movie_in_output = args.keep_input_movie_in_output

    print("nb_frame_training :"+str(nb_frame_training))

    if copy_input_file_scratch: 
        input_movie_s3 = input_movie_path
        movie_path = results_folder+'input_ophys_experiment.h5'
    
        if not os.path.isfile(movie_path):
            print("Copying S3 file locally")
            shutil.copy(input_movie_s3, movie_path)
            print("Done copying S3 file locally")
    else:
        movie_path = input_movie_path

    # Initialize meta-parameters objects
    finetuning_params = {}
    generator_param = {}
    generator_test_param = {}

    # Those are parameters used for the Validation test generator.
    # Here the test is done on the beginning of the data but
    # this can be a separate file
    generator_param["name"] = "OphysGenerator"  # Name of object
    # in the collection
    generator_param["pre_frame"] = 30
    generator_param["post_frame"] = 30
    generator_param["data_path"] = movie_path
    generator_param["batch_size"] = 5
    generator_param["start_frame"] = 0
    generator_param["end_frame"] = -1
    generator_param["total_samples"] = nb_frame_training
    generator_param["pre_post_omission"] = 0  # Number of frame omitted before and after the predicted frame

    generator_test_param["name"] = "OphysGenerator"  # Name of object
    # in the collection
    generator_test_param["pre_frame"] = 30
    generator_test_param["post_frame"] = 30
    generator_test_param["data_path"] = movie_path
    generator_test_param["batch_size"] = 5
    generator_test_param["start_frame"] = 0
    generator_test_param["end_frame"] = -1
    generator_test_param["total_samples"] = 50

    generator_test_param["pre_post_omission"] = 0  # Number of frame omitted before and after the predicted frame

    # Those are parameters used for the training process
    finetuning_params["name"] = "transfer_trainer"

    # Change this path to any model you wish to improve
    finetuning_params["model_source"] = {
        "local_path": input_model_path
    }

    # An epoch is defined as the number of batches pulled from the dataset.
    # Because our datasets are VERY large. Often, we cannot
    # go through the entirety of the data so we define an epoch
    # slightly differently than is usual.
    steps_per_epoch = int(nb_frame_training/5)
    finetuning_params["steps_per_epoch"] = steps_per_epoch
    finetuning_params[
        "period_save"
    ] = 25
    # network model is potentially saved during training between a regular
    # nb epochs

    finetuning_params["learning_rate"] = 0.0001
    finetuning_params["loss"] = "mean_squared_error"
    finetuning_params["output_dir"] = results_folder
    finetuning_params["use_multiprocessing"] = True
    finetuning_params["measure_baseline_loss"] = False
    finetuning_params["caching_validation"] = True

    args = {
        "finetuning_params": finetuning_params,
        "generator_params": generator_param,
        "test_generator_params": generator_test_param,
        "output_full_args": True
    }

    finetuning_obj = FineTuning(input_data=args, args=[])
    
    print("Starting fine-tuning")
    
    finetuning_obj.run()
    
    print("Fine-tuning finished")
    del(finetuning_obj)

    if copy_input_file_scratch: 
        if not(keep_input_movie_in_output):
            if os.path.isfile(movie_path):
                print("Deleting local movie copy")
                os.remove(movie_path)


    fine_tune_model_path = glob.glob(os.path.join(results_folder, "*_transfer_model.h5"))[0]

    # This is to make the output model standardized filename
    print("Copying S3 file locally")
    shutil.move(fine_tune_model_path, results_folder+'fine_tuned_model.h5')
    print("Done copying S3 file locally")
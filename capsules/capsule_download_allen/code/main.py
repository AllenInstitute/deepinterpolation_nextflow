import argparse
import json
results_folder = "../results/"
data_folder = "../data/"
import boto3

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--json_file_input", type=str, default="../data/list_files/movie_param1.json")
    parser.add_argument("--h5_file_output", type=str, default="../results/experiment.h5")
    
    args = parser.parse_args()
    json_file_input = args.json_file_input
    h5_file_output = args.h5_file_output

    # Opening JSON file
    with open(json_file_input) as file_handle:
        # returns JSON object as 
        # a dictionary
        metadata_nwb = json.load(file_handle)

    bucket_name = metadata_nwb['bucket']
    file_name = metadata_nwb['bucket_filename']

    # Connect to the S3 bucket. modify below to use your own bucket with a private key
    s3 = boto3.resource('s3', aws_access_key_id='None', aws_secret_access_key='None')

    bucket = s3.Bucket(bucket_name)

    bucket.download_file(file_name, h5_file_output)
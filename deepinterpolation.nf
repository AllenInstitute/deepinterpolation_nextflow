#!/usr/bin/env nextflow
nextflow.enable.dsl = 1

json_inputs_ranges_to_capsule_inference = channel.fromPath("./input/frame_range/*", type: 'any', relative: true)
small_list_to_download_locally = channel.fromPath("./input/movie_s3/*", type: 'any', relative: true)
capsule_download_allen_to_capsule_finetuning_allen = channel.create()
capsule_finetuning_allen_to_capsule_inference = channel.create()
capsule_inference_to_capsule_movie_merger = channel.create()
capsule_movie_merger_to_capsule_suite2p = channel.create()

// capsule - calcium imaging + deepinterp inf - v1
process capsule_inference {
	tag 'capsule_inference'
	container '245412653747/deep_interpolation_nextflow:inference'

	cpus 2
	memory '40 GB'

	input:
	tuple val(id_movie), path('capsule/data/fine_tuning/') from capsule_finetuning_allen_to_capsule_inference
	each path2 from json_inputs_ranges_to_capsule_inference

	output:
	tuple val(id_movie), path('capsule/results/*') into capsule_inference_to_capsule_movie_merger

	script:
	"""
	#!/usr/bin/env bash
	set -e

	mkdir -p capsule
	mkdir -p capsule/data
	mkdir -p capsule/results
	mkdir -p capsule/scratch
	mkdir -p capsule/data/List_of_frames_intervals

	ln -s /home/jeromel/nextflow/input/frame_range/$path2 capsule/data/List_of_frames_intervals/input_range.json # id: 98967a19-1088-4e73-9796-0c6490e2ce55
	
	echo "[${task.tag}] cloning git repo..."
	git clone "https://github.com/AllenInstitute/deepinterpolation_nextflow.git" capsule-repo
	mv capsule-repo/capsules/capsule_inference/code capsule/code
	rm -rf capsule-repo

	echo "[${task.tag}] running capsule..."
	cd capsule/code
	chmod +x run
	./run --cache_input_data --copy_input_file_scratch --input_frame_range ../data/List_of_frames_intervals/input_range.json --inference_model_path ../data/fine_tuning/fine_tuned_model.h5 --input_movie_path ../data/fine_tuning/input_ophys_experiment.h5

	echo "[${task.tag}] completed!"
	"""
}

// capsule - Movie merger
process capsule_movie_merger {
	tag 'capsule_movie_merger'
	container '245412653747/deep_interpolation_nextflow:merging'

	cpus 2
	memory '64 GB'

	input:
	tuple val(id_movie), path('capsule/data/merge/') from capsule_inference_to_capsule_movie_merger.groupTuple()

	output:
	tuple val(id_movie), path('capsule/results/*') into capsule_movie_merger_to_capsule_suite2p

	script:
	"""
	#!/usr/bin/env bash
	set -e

	mkdir -p capsule
	mkdir -p capsule/data
	mkdir -p capsule/results
	mkdir -p capsule/scratch

	echo "[${task.tag}] cloning git repo..."
	git clone "https://github.com/AllenInstitute/deepinterpolation_nextflow.git" capsule-repo
	mv capsule-repo/capsules/capsule_movie_merger/code capsule/code
	rm -rf capsule-repo

	echo "[${task.tag}] running capsule..."
	cd capsule/code
	chmod +x run
	./run 

	echo "[${task.tag}] completed!"
	"""
}

// capsule - Calcium imaging + deepinterp tuning
process capsule_finetuning_allen {
	tag 'capsule_finetuning_allen'
	container '245412653747/deep_interpolation_nextflow:finetuning_allen'

	cpus 32
	memory '64 GB'

	input:
	tuple val(id_movie), path('capsule/data/ophys_experiment.h5') from capsule_download_allen_to_capsule_finetuning_allen

	output:
	tuple val(id_movie), path('capsule/results/*') into capsule_finetuning_allen_to_capsule_inference

	script:
	"""
	#!/usr/bin/env bash
	set -e

	mkdir -p capsule
	mkdir -p capsule/data
	mkdir -p capsule/results
	mkdir -p capsule/scratch

	ln -s '/home/jeromel/nextflow/input/2021_07_31_09_49_38_095550_unet_1024_search_mean_squared_error_pre_30_post_30_feat_32_power_1_depth_4_unet_True-0125-0.5732.h5' capsule/data/deepInterpolation_input_model.h5 # id: 2688c8ce-32b3-48c7-8e92-2d3a2a9de817
	
	echo "[${task.tag}] cloning git repo..."
	git clone "https://github.com/AllenInstitute/deepinterpolation_nextflow.git" capsule-repo
	mv capsule-repo/capsules/capsule_finetuning_allen/code capsule/code
	rm -rf capsule-repo

	echo "[${task.tag}] running capsule..."
	cd capsule/code
	chmod +x run
	./run --keep_input_movie_in_output --copy_input_file_scratch --input_model_path ../data/deepInterpolation_input_model.h5 --input_movie_path ../data/ophys_experiment.h5 --nb_frame_training 10000

	echo "[${task.tag}] completed!"
	"""
}

// capsule - calcium imaging + suite2p segmentation - v1
process capsule_suite2p {
	tag 'capsule_suite2p'
	container '245412653747/deep_interpolation_nextflow:suite2p'
	cpus 16
	memory '100 GB'

	publishDir "$RESULTS_PATH/$id_movie", saveAs: { filename -> new File(filename).getName() }

	input:
	tuple val(id_movie), path('capsule/data/') from capsule_movie_merger_to_capsule_suite2p
	val index from 1..10000

	output:
	path 'capsule/results/*'

	script:
	"""
	#!/usr/bin/env bash
	set -e

	mkdir -p capsule
	mkdir -p capsule/data
	mkdir -p capsule/results
	mkdir -p capsule/scratch

	echo "[${task.tag}] cloning git repo..."
	git clone "https://github.com/AllenInstitute/deepinterpolation_nextflow.git" capsule-repo
	mv capsule-repo/capsules/capsule_suite2p/code capsule/code
	rm -rf capsule-repo

	echo "[${task.tag}] running capsule..."
	cd capsule/code
	chmod +x run
	./run --input_movie_path ../data/merged_movie.h5 --sampling_rate 30 --suite2p_threshold_scaling 1.5

	echo "[${task.tag}] completed!"
	"""
}

// capsule - download dandi nwb file locally
process capsule_download_allen {
	tag 'capsule_download_allen'
	container '245412653747/deep_interpolation_nextflow:download_allen'

	cpus 4
	memory '32 GB'

	input:
	val path7 from small_list_to_download_locally

	output:
	tuple val(path7), path('capsule/results/experiment.h5') into capsule_download_allen_to_capsule_finetuning_allen

	script:
	"""
	#!/usr/bin/env bash
	set -e

	mkdir -p capsule
	mkdir -p capsule/data
	mkdir -p capsule/results
	mkdir -p capsule/scratch
	
	ln -s '/home/jeromel/nextflow/input/movie_s3/$path7' ./capsule/data/movie_param.json # id: 9b848d33-3980-412c-8752-d7f6d6007eff
	
	echo "[${task.tag}] cloning git repo..."
	git clone "https://github.com/AllenInstitute/deepinterpolation_nextflow.git" capsule-repo
	mv capsule-repo/capsules/capsule_download_allen/code capsule/code
	rm -rf capsule-repo
	
	echo "[${task.tag}] running capsule..."
	cd capsule/code
	chmod +x run
	./run --json_file_input ../data/movie_param.json --h5_file_output ../results/experiment.h5

	echo "[${task.tag}] completed!"
	"""
}

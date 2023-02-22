[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)

Deepinterpolation nextflow pipeline
========================
This repository contains code to replicate a denoising+segmentation pipeline either on a local machine, SLURM cluster or make an AWS cloud deployment. 
It relies on Nextflow capabilities to achieve that goal and is pulling docker repositories in the process. Specific deployments could require setting up the nextflow.config file. 
We provide an example nextflow.config file for deployment to a SLURM cluster. 

Running deepinterpolation nextflow pipeline
========================
1. Install nextflow at the root of the repository using 

```curl -s https://get.nextflow.io | bash```

For more instructins, see https://www.nextflow.io/docs/latest/getstarted.html

2. Once installed, run individual nextflow files as : 

```./nextflow deepinterpolation.nf```

nf files contains all required instruction to pull environments (dockers, ...) and launch the underlying figures code.

The provided .config file is written to work on a SLURM cluster, below is an example .config file, if you are running this locally using a docker daemon: 

```
  docker {
      enabled = true
      runOptions = '--pull=always'
      runOptions= "-v $HOME:$HOME"
  }
```

Notes
========================
Please reach out jeromel@alleninstitute.org for any questions. If this is useful to you, :wave: are welcome!
Credits are due to [David Feng](https://github.com/dyf) and the Code Ocean team. This repo results from the work of a lot of people. 

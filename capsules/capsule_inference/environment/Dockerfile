# hash:sha256:f1284af466adc512b9375c883b86b582f10025501b668abc240ec511497f3599
FROM registry.codeocean.allenneuraldynamics.org/codeocean/tensorflow-training:2.6.2-gpu-py38-cu112-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN pip install git+https://github.com/AllenInstitute/deepinterpolation.git@40f8d33068887f85881f0e33646380d9e8fa62a2
RUN pip install suite2p==0.10.1
RUN pip install matplotlib==3.1.3
RUN pip install pynwb
# RUN pip install line_profiler


# RUN pip install protobuf==3.20.*
# RUN conda install -c nvidia cuda-nvcc
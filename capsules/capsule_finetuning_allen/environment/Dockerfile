# hash:sha256:f1284af466adc512b9375c883b86b582f10025501b668abc240ec511497f3599
FROM registry.codeocean.allenneuraldynamics.org/codeocean/tensorflow-training:2.6.2-gpu-py38-cu112-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN pip install git+https://github.com/AllenInstitute/deepinterpolation.git@4265c2be20e60dbcf8c98b4b06f0b7954761e30d
RUN pip install suite2p==0.10.1
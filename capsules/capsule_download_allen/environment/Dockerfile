# hash:sha256:856a45bbdb67bd6de99e104a6a953f9cd0c5e9343b7c6e7e1bc6a43f36c5c4c4
FROM registry.codeocean.allenneuraldynamics.org/codeocean/jupyterlab:3.0.9-miniconda4.9.2-python3.8-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN pip3 install -U --no-cache-dir \
    boto3==1.26.31

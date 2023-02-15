# hash:sha256:569d6f5e7c0f1373a21cbd4009c8fe036b67ba4c5bb26ba553c6ee93246f2349
FROM registry.codeocean.allenneuraldynamics.org/codeocean/kilosort2_5-compiled-base:latest

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN pip install -U --no-cache-dir \
    pynwb==2.2.0 \
    suite2p==0.11.1

COPY postInstall /
RUN /postInstall

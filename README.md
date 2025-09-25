# Tachyon Kinesis Streaming Sample
This repository shows how to stream video to the [AWS Kinesis Video Stream service](https://aws.amazon.com/kinesis/video-streams/). It uses a Docker image that contains [OpenCV](https://opencv.org/) built with [gstreamer](https://gstreamer.freedesktop.org/) support as well as the [kvssink gstreamer plugin](https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp). 

For demonstration purposes, the stream is first annotated using the Yolo v8 library before being passed into the stream. 

<img width="1247" height="766" alt="Annotated stream" src="https://github.com/user-attachments/assets/3550c7bd-4710-49f8-a96b-ba6c3026e5ba" />

To run:
- Fill out the credentials `THING_NAME, AWS_REGION, IOT_CRED_ENDPOINT, and ROLE_ALIAS`
- Add AWS IoT certificates into `./certs`
- Run: `particle container run`

<img height="500" alt="Hardware" src="https://github.com/user-attachments/assets/0ac8e38e-d1d1-45a5-9be4-180e1f1468a8" />

The base Docker image can be [found on DockerHub](https://hub.docker.com/r/epietrowicz/kvs-producer-gst-opencv) and is built as follows:

```
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
# keep CMake from auto-parallelizing
ENV CMAKE_BUILD_PARALLEL_LEVEL=1

RUN apt-get update
RUN apt-get install -y git cmake pkgconf m4 build-essential

RUN apt-get install -y --no-install-recommends \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-plugins-base-apps \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone --depth 1 https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp kvs
WORKDIR /opt/kvs
RUN mkdir -p build
WORKDIR /opt/kvs/build

RUN cmake .. \ 
    -DBUILD_GSTREAMER_PLUGIN=ON \
    -DBUILD_JNI=OFF \
    -DBUILD_TEST=OFF \
    -DBUILD_SAMPLES=OFF

RUN make

WORKDIR /opt
# Build and install OpenCV from source
# Update needs to run again for some reason?
RUN apt-get update
RUN apt install python3-pip -y

ENV OPENCV_VER="88"
ENV ENABLE_CONTRIB=0
ENV ENABLE_HEADLESS=1
ENV CMAKE_ARGS="-DWITH_GSTREAMER=ON"

RUN git clone \
    --branch ${OPENCV_VER} \
    --depth 1 \
    --recurse-submodules \
    --shallow-submodules \
    https://github.com/opencv/opencv-python.git \
    opencv-python-${OPENCV_VER}

WORKDIR /opt/opencv-python-${OPENCV_VER}

ENV PIP_BREAK_SYSTEM_PACKAGES=1

RUN python3 -m pip wheel . --verbose
RUN python3 -m pip install opencv_python*.whl

ENV GST_PLUGIN_PATH=/opt/kvs/build
ENV LD_LIBRARY_PATH=/opt/kvs/open-source/local/lib

WORKDIR /app
```

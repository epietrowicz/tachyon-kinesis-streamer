FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update

RUN apt-get install -y \
    cmake \
    m4 \
    git \
    build-essential

RUN apt-get install -y \
    libssl-dev \
    libcurl4-openssl-dev \
    liblog4cplus-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-plugins-base-apps \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools && \
    rm -rf /var/lib/apt/lists/*

# Build and install Kinesis
RUN git clone https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp.git
RUN mkdir -p ./amazon-kinesis-video-streams-producer-sdk-cpp/build
WORKDIR /amazon-kinesis-video-streams-producer-sdk-cpp/build

# Long running
RUN cmake .. -DBUILD_GSTREAMER_PLUGIN=ON

RUN make

RUN mkdir /amazon-kinesis-video-streams-producer-sdk-cpp/build/certs
COPY certs /amazon-kinesis-video-streams-producer-sdk-cpp/build/certs

WORKDIR /amazon-kinesis-video-streams-producer-sdk-cpp

WORKDIR /

# Build and install OpenCV from source
# Update needs to run again for some reason?
RUN apt-get update
RUN apt install python3-pip -y

ENV OPENCV_VER="80"
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

WORKDIR /opencv-python-${OPENCV_VER}

RUN python3 -m pip wheel . --verbose
RUN python3 -m pip install opencv_python*.whl

RUN apt-get install -y ubuntu-restricted-extras

COPY src /src
COPY certs /certs
WORKDIR /src

ENV GST_PLUGIN_PATH=/amazon-kinesis-video-streams-producer-sdk-cpp/build/
ENV LD_LIBRARY_PATH=/amazon-kinesis-video-streams-producer-sdk-cpp/open-source/local/lib

ENV AWS_DEFAULT_REGION=us-east-1
ENV CERT_PATH=certs/certificate.pem.crt
ENV PRIVATE_KEY_PATH=certs/private.pem.key
ENV CA_CERT_PATH=certs/AmazonRootCA1.pem
ENV ROLE_ALIAS=CameraIoTRoleAlias
ENV IOT_GET_CREDENTIAL_ENDPOINT=c666b3zjb4za4.credentials.iot.us-east-1.amazonaws.com

CMD ["/bin/bash"]
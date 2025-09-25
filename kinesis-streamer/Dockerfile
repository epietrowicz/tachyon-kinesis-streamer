FROM epietrowicz/kvs-producer-gst-opencv

# Don't let Ultralytics overwrite base image opencv-python that's been built with gstreamer
RUN pip3 install --no-deps ultralytics \
 && pip3 install --no-deps --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio \
 && pip3 install numpy pillow matplotlib pyyaml tqdm psutil thop onnx onnxsim
 
CMD ["python3", "src/main.py"]

import os
import cv2
import time

# ---- Configuration ----
STREAM_NAME = "tachyon_test"
AWS_REGION = "us-east-1"

DEVICE_CERTIFICATE_PATH = "./certificates/device-certificate.pem.crt"
PRIVATE_KEY_PATH = "./certificates/private-key.pem.key"
ROOT_CA_PATH = "./certificates/root-ca.pem"
ROLE_ALIAS = "TachyonIoTRoleAlias"
IOT_CRED_ENDPOINT = "afevc2yjrmfjb-ats.iot.us-east-1.amazonaws.com"
THING_NAME = "tachyon_test"

# Camera parameters
CAMERA_INDEX = 2  # /dev/video2
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS = 30
BITRATE_KBPS = 2000  # video bitrate for x264 encoder

# ---- Open camera ----
cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_ANY)
if not cap.isOpened():
    raise RuntimeError(f"Could not open camera index {CAMERA_INDEX}")

# Set desired caps (best-effort)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, FPS)

# Query actual caps
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS) or FPS

print(f"Camera opened: {w}x{h} @ {fps:.2f} fps")

# ---- Build GStreamer pipeline for KVS ----
# We will feed frames into OpenCV's VideoWriter using a GStreamer pipeline that ends at kvssink.
# Notes:
#  - appsrc: receives raw frames from OpenCV
#  - videoconvert: ensure colorspace compatibility
#  - x264enc: encodes to H.264 (baseline, low latency)
#  - h264parse: preps the stream
#  - kvssink: sends to Kinesis Video Streams (uses your AWS creds / region)

bitrate_bps = BITRATE_KBPS * 1000

gst_pipeline = (
    "appsrc ! "
    "videoconvert ! "
    f"x264enc tune=zerolatency bitrate={BITRATE_KBPS} speed-preset=veryfast key-int-max={int(fps*2)} ! "
    "video/x-h264,profile=baseline,stream-format=avc,alignment=au ! "
    "h264parse ! "
    # ---- kvssink with IoT certificate auth ----
    f'kvssink stream-name="{STREAM_NAME}" aws-region="{AWS_REGION}" storage-size=128 '
    'iot-certificate="'
    f"iot-certificate,"
    f"endpoint={IOT_CRED_ENDPOINT},"
    f"cert-path={DEVICE_CERTIFICATE_PATH},"
    f"key-path={PRIVATE_KEY_PATH},"
    f"ca-path={ROOT_CA_PATH},"
    f"role-aliases={ROLE_ALIAS},"
    f"iot-thing-name={THING_NAME}"
    '"'
)

# OpenCV needs fourcc=0 and CAP_GSTREAMER for pipeline sinks
writer = cv2.VideoWriter(
    gst_pipeline, cv2.CAP_GSTREAMER, 0, fps, (w, h), True  # fourcc ignored by GStreamer
)

if not writer.isOpened():
    cap.release()
    raise RuntimeError(
        "Failed to open GStreamer/kvssink pipeline. "
        "Ensure OpenCV has GStreamer and kvssink is installed."
    )

print(f"Streaming to Kinesis Video Stream: {STREAM_NAME} ({AWS_REGION})")
print("Press Ctrl+C to stop.")

# ---- Main loop ----
try:
    # Give kvssink a moment to initialize
    time.sleep(0.5)

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Frame grab failed; exiting.")
            break

        # IMPORTANT: appsrc expects BGR by default here (videoconvert handles colorspace). Just write the frame.
        writer.write(frame)

        # Optional preview window (comment out for headless)
        # cv2.imshow("Preview", frame)
        # if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
        #     break

except KeyboardInterrupt:
    print("\nStopping stream...")

finally:
    writer.release()
    cap.release()
    cv2.destroyAllWindows()
    print("Cleaned up.")

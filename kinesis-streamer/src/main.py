import os, cv2, time
from ultralytics import YOLO

# Use absolute paths
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEVICE_CERTIFICATE_PATH = os.path.join(BASE, "certs/device-certificate.pem.crt")
PRIVATE_KEY_PATH        = os.path.join(BASE, "certs/private-key.pem.key")
ROOT_CA_PATH            = os.path.join(BASE, "certs/root-ca.pem")

THING_NAME        = ""
STREAM_NAME = THING_NAME
AWS_REGION  = ""
IOT_CRED_ENDPOINT = ""
ROLE_ALIAS      = ""

INFER_EVERY = 60  # run inference on every Nth frame

WIDTH, HEIGHT, FRAMERATE = 640, 480, 15

kvssink_auth = (
    "iot-certificate,"
    f"endpoint={IOT_CRED_ENDPOINT},"
    f"cert-path={DEVICE_CERTIFICATE_PATH},"
    f"key-path={PRIVATE_KEY_PATH},"
    f"ca-path={ROOT_CA_PATH},"
    f"role-aliases={ROLE_ALIAS},"
    f"iot-thing-name={THING_NAME}"
)

raw_caps = f"video/x-raw,format=BGR,width={WIDTH},height={HEIGHT},framerate={FRAMERATE}/1"

# https://docs.aws.amazon.com/kinesisvideostreams/latest/dg/examples-gstreamer-plugin.html#examples-gstreamer-plugin-launch
pipeline = (
    f"appsrc is-live=true do-timestamp=true format=time caps={raw_caps} ! "
    "videoconvert ! "
    "video/x-raw,format=I420,width=640,height=480,framerate=15/1 ! "
    "x264enc bframes=0 key-int-max=45 bitrate=500 tune=zerolatency speed-preset=veryfast ! "
    "video/x-h264,stream-format=avc,alignment=au,profile=baseline ! "
    "h264parse config-interval=-1 ! "
    f'kvssink stream-name="{STREAM_NAME}" storage-size=512 aws-region="{AWS_REGION}" '
    f'iot-certificate="{kvssink_auth}"'
)

capture = cv2.VideoCapture(2)
out = cv2.VideoWriter(pipeline, cv2.CAP_GSTREAMER, 0, float(FRAMERATE), (WIDTH, HEIGHT), True)

if not out.isOpened():
    raise RuntimeError("Failed to open GStreamer VideoWriter. Check kvssink/x264enc availability and your pipeline.")

period = 1.0 / FRAMERATE
font   = cv2.FONT_HERSHEY_SIMPLEX

model = YOLO("yolov8n.pt") 

def run_yolo(frame):
    results = model.predict(frame, verbose=False)[0]
    boxes = []
    if results.boxes is not None :
        for b in results.boxes:
            # xyxy, confidence, class
            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            conf = float(b.conf[0].item())
            if conf < 0.7:
                continue
            cls  = int(b.cls[0].item())
            label = f"{model.names.get(cls, str(cls))} {conf:.2f}"
            boxes.append((x1, y1, x2, y2, label))
    return boxes

frame_idx = 0
last_boxes = []

while True:
    ok, frame = capture.read()
    if not ok:
        # brief backoff if camera hiccups
        time.sleep(0.01)
        print("No frame")
        continue

    # Run YOLO (returns results for one image)
    do_infer = (frame_idx % INFER_EVERY == 0)

    if do_infer:
        last_boxes = run_yolo(frame)

    # Draw whichever boxes we have (fresh or reused)
    for (x1, y1, x2, y2, label) in last_boxes:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
        (tw, th), bl = cv2.getTextSize(label, font, 0.5, 1)
        cv2.rectangle(frame, (x1, max(0, y1 - th - 6)), (x1 + tw + 6, y1), (0,255,0), -1)
        cv2.putText(frame, label, (x1 + 3, y1 - 4), font, 0.5, (0,0,0), 1, cv2.LINE_AA)

    # Push annotated frame to appsrc via OpenCV
    out.write(frame)
    frame_idx += 1

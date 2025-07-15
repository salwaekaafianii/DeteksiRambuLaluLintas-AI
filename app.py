from flask import Flask, render_template, Response
import datetime  
import cv2
import base64
import threading
import time
import requests
import json

# === Konfigurasi API Roboflow ===
API_KEY = "XhKO3mOOqNCSdMB89yl6"
MODEL_URL = f"https://detect.roboflow.com/traffic-sign-indonesia/2?api_key={API_KEY}"

# === YOLO Lokal ===
# from ultralytics import YOLO
# model = YOLO("runs/detect/rambu-model/weights/best.pt")
# print("Model lokal dimuat, jumlah kelas:", model.names)

app = Flask(__name__)
camera = cv2.VideoCapture(0) # aktifkan kamera (index 0 = webcam utama)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

latest_predictions = [] # list untuk menyimpan hasil deteksi terbaru
last_frame = None
detection_interval = 0.2 # waktu jeda antar deteksi (dalam detik)E

def detect_thread():
    global latest_predictions, last_frame

    while True:
        if last_frame is not None:
            # === MODE ROBOTFLOW ===
            frame = cv2.resize(last_frame, (416, 416))
            _, buffer = cv2.imencode('.jpg', frame)
            b64_img = base64.b64encode(buffer).decode()# encode ke base64 string
            try:
                # kirim frame ke Roboflow API
                response = requests.post(
                    MODEL_URL,
                    data=b64_img,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                # jika berhasil
                if response.status_code == 200:
                    preds = response.json().get("predictions", []) # ambil prediksi
                    timestamp = datetime.datetime.now().timestamp() # catat waktu deteksi
                    # filter confidence >= 0.6
                    preds = [p for p in preds if p.get("confidence", 0) >= 0.6]
                    latest_predictions = [{**pred, "timestamp": timestamp} for pred in preds] if preds else []

                else:
                    print(f"[Roboflow Error] {response.status_code}: {response.text}")
                    latest_predictions = []
            except Exception as e:
                print(f"[Exception] {e}")
                latest_predictions = []

            # === MODE LOCAL ===
            # print("[DEBUG] YOLO lokal memproses frame...")
            # results = model.predict(last_frame, imgsz=416, conf=0.7)[0]
            # preds = []
            # timestamp = datetime.datetime.now().timestamp()

            # for box in results.boxes:
            #     confidence = box.conf[0].item()
            #     if confidence < 0.7:
            #         continue  # skip prediksi dengan confidence rendah

            #     x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            #     label_id = int(box.cls[0].item())
            #     label = model.names[label_id]
            #     preds.append({
            #         "x1": int(x1), "y1": int(y1),
            #         "x2": int(x2), "y2": int(y2),
            #         "class": label, "confidence": confidence,
            #         "timestamp": timestamp
            #     })

            # latest_predictions = preds
            # print(f"[DEBUG] Jumlah prediksi valid: {len(preds)}")
       
        time.sleep(detection_interval)

def generate_frames():
    global last_frame, latest_predictions
    while True:
        success, frame = camera.read()
        if not success:
            break

        last_frame = frame.copy()
        h, w, _ = frame.shape
        current_time = datetime.datetime.now().timestamp() 
        max_age = 0.5 
        if not latest_predictions:
            print("[DEBUG] Tidak ada prediksi, bounding box tidak digambar")

        for pred in latest_predictions:
            if current_time - pred.get("timestamp", 0) > max_age:
                continue   
            if pred.get("confidence", 0) < 0.7:
                continue

            # === MODE ROBOTFLOW ===
            # bounding box dalam format (x, y, width, height) 
            if "x" in pred:
                x = int(pred["x"] / 416 * w)
                y = int(pred["y"] / 416 * h)
                width = int(pred["width"] / 416 * w)
                height = int(pred["height"] / 416 * h)
                x1 = int(x - width / 2)
                y1 = int(y - height / 2)
                x2 = int(x + width / 2)
                y2 = int(y + height / 2)

            # === MODE LOKAL ===
            else:
                x1, y1, x2, y2 = pred["x1"], pred["y1"], pred["x2"], pred["y2"]

            shrink_ratio = 0.1
            width = x2 - x1
            height = y2 - y1
            pad_w = int(width * shrink_ratio / 2)
            pad_h = int(height * shrink_ratio / 2)

            x1_new = x1 + pad_w
            y1_new = y1 + pad_h
            x2_new = x2 - pad_w
            y2_new = y2 - pad_h

            if x2_new <= x1_new or y2_new <= y1_new:
                x1_new, y1_new, x2_new, y2_new = x1, y1, x2, y2

            x1, y1, x2, y2 = x1_new, y1_new, x2_new, y2_new

            x1 = max(0, min(x1, w - 1))
            y1 = max(0, min(y1, h - 1))
            x2 = max(0, min(x2, w - 1))
            y2 = max(0, min(y2, h - 1))

            label = pred["class"]
            confidence = pred.get("confidence", 0)
            label_text = f"{label} ({confidence*100:.1f}%)"

            print(f"[TERDETEKSI] {label_text} di posisi: ({x1},{y1}) - ({x2},{y2})")

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.putText(frame, label_text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

#route halaman utama        
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/start-camera')
def start_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        time.sleep(0.5)
    return '', 204

@app.route('/stop-camera')
def stop_camera():
    global camera
    if camera and camera.isOpened():
        camera.release()
        camera = None
    return '', 204
# streaming Deteksi (Text) – untuk frontend JS
@app.route('/detection-stream')
def detection_stream():
    def generate():
        last_timestamp = 0
        while True:
            if latest_predictions:
                for pred in latest_predictions:
                    if pred.get("timestamp", 0) > last_timestamp:
                        data = {
                            "label": pred.get("class", "Tidak Diketahui"),
                            "confidence": pred.get("confidence", 0.0)
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                        last_timestamp = pred.get("timestamp", 0)
            time.sleep(1)
    return Response(generate(), mimetype='text/event-stream')


if __name__ == "__main__":
    threading.Thread(target=detect_thread, daemon=True).start()
    app.run(debug=True)

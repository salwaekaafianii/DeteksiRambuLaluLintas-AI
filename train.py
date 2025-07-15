from ultralytics import YOLO

# Load model kecil (nano) agar cepat
model = YOLO("yolov8n.pt")

# Latih model
model.train(
    data="Traffic-Sign-Indonesia-3/data.yaml",  
    epochs=10,       
    imgsz=416,       
    batch=8,         
    name="rambu-model"
)

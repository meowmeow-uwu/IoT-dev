import cv2
import threading
import urllib.request
import numpy as np
import os
from time import sleep
from flask import Flask, Response, render_template_string, jsonify

app = Flask(__name__)

# Biến dùng chung
latest_frame = None
face_boxes = []
img_counter = 0

# Tải ảnh Filter PNG (Nếu có trong thư mục, nếu không code sẽ tự vẽ)
hat_img = cv2.imread('hat.png', cv2.IMREAD_UNCHANGED)
glasses_img = cv2.imread('glasses.png', cv2.IMREAD_UNCHANGED)
beard_img = cv2.imread('beard.png', cv2.IMREAD_UNCHANGED)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Photobooth - AR Filters</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { text-align: center; font-family: Arial, sans-serif; background-color: #1e1e1e; color: white; margin: 0; padding: 20px; }
        h1 { margin-bottom: 20px; color: #4CAF50; }
        .camera-container { border: 5px solid #333; border-radius: 10px; display: inline-block; overflow: hidden; background: #000; }
        img { max-width: 100%; height: auto; display: block; height: 600px; }
        .btn-capture { margin-top: 20px; padding: 15px 40px; font-size: 20px; font-weight: bold; background-color: #ff4757; color: white; border: none; border-radius: 50px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: 0.2s; }
        .btn-capture:hover { background-color: #ff6b81; transform: scale(1.05); }
        .btn-capture:active { background-color: #ff4757; transform: scale(0.95); }
        #status { margin-top: 15px; font-size: 18px; color: #2ed573; height: 20px; }
    </style>
</head>
<body>
    <h1>📸 Photobooth (AR Mũ, Kính, Râu)</h1>
    
    <div class="camera-container">
        <!-- Chỗ này sẽ hiện Filter trực tiếp để bạn xem trước -->
        <img src="/video_feed" alt="Đang kết nối Camera..." />
    </div>
    
    <br>
    <button class="btn-capture" onclick="captureImage()">📷 CHỤP ẢNH</button>
    <p id="status"></p>

    <script>
        function captureImage() {
            fetch('/capture')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').innerText = data.message;
                    setTimeout(() => { document.getElementById('status').innerText = ""; }, 3000);
                });
        }
    </script>
</body>
</html>
"""

# ==========================================
# HÀM TRỘN ẢNH TRONG SUỐT (ALPHA BLENDING)
# ==========================================
def overlay_transparent(background, overlay, x, y):
    bg_h, bg_w, _ = background.shape
    h, w, _ = overlay.shape

    # Giới hạn tọa độ không vượt quá khung hình
    y1, y2 = max(0, y), min(bg_h, y + h)
    x1, x2 = max(0, x), min(bg_w, x + w)
    y1o, y2o = max(0, -y), min(h, bg_h - y)
    x1o, x2o = max(0, -x), min(w, bg_w - x)

    if y1 >= y2 or x1 >= x2 or y1o >= y2o or x1o >= x2o:
        return background

    # Trộn ảnh dựa trên kênh Alpha (độ trong suốt)
    overlay_image = overlay[y1o:y2o, x1o:x2o, :3]
    alpha = overlay[y1o:y2o, x1o:x2o, 3] / 255.0

    for c in range(3):
        background[y1:y2, x1:x2, c] = (alpha * overlay_image[:, :, c] + (1 - alpha) * background[y1:y2, x1:x2, c])
    return background

# ==========================================
# HÀM GẮN FILTER LÊN KHUÔN MẶT
# ==========================================
def apply_filters(frame, faces):
    for (x, y, w, h) in faces:
        # Nếu chưa có file PNG, vẽ hoạt hình thay thế (Fallback)
        if hat_img is None or glasses_img is None or beard_img is None:
            # Vẽ Kính tròn
            cv2.circle(frame, (int(x + w*0.3), int(y + h*0.4)), int(w*0.15), (0, 0, 0), 4)
            cv2.circle(frame, (int(x + w*0.7), int(y + h*0.4)), int(w*0.15), (0, 0, 0), 4)
            cv2.line(frame, (int(x + w*0.45), int(y + h*0.4)), (int(x + w*0.55), int(y + h*0.4)), (0, 0, 0), 4)
            # Vẽ Râu quai nón
            cv2.ellipse(frame, (int(x + w*0.5), int(y + h*0.75)), (int(w*0.25), int(h*0.1)), 0, 0, 180, (50, 50, 50), -1)
            # Vẽ Mũ Top Hat
            cv2.rectangle(frame, (int(x), int(y - h*0.4)), (int(x + w), int(y)), (150, 50, 50), -1)
            cv2.rectangle(frame, (int(x - w*0.2), int(y)), (int(x + w*1.2), int(y + h*0.05)), (150, 50, 50), -1)
        else:
            # Nếu có file PNG, dán ảnh thật lên!
            # 1. Dán Mũ
            hat_w = int(w * 1.2)
            hat_h = int(hat_w * hat_img.shape[0] / hat_img.shape[1])
            hat_resized = cv2.resize(hat_img, (hat_w, hat_h))
            frame = overlay_transparent(frame, hat_resized, x - int(w*0.1), y - int(hat_h*0.8))
            
            # 2. Dán Kính
            glass_w = int(w * 0.95)
            glass_h = int(glass_w * glasses_img.shape[0] / glasses_img.shape[1])
            glass_resized = cv2.resize(glasses_img, (glass_w, glass_h))
            frame = overlay_transparent(frame, glass_resized, x + int(w*0.025), y + int(h*0.2))
            
            # 3. Dán Râu
            beard_w = int(w * 0.8)
            beard_h = int(beard_w * beard_img.shape[0] / beard_img.shape[1])
            beard_resized = cv2.resize(beard_img, (beard_w, beard_h))
            frame = overlay_transparent(frame, beard_resized, x + int(w*0.1), y + int(h*0.6))
    return frame

# ==========================================
# LUỒNG 1: HÚT VIDEO HTTP & XOAY
# ==========================================
def fetch_stream_thread():
    global latest_frame
    stream_url = "http://192.168.137.24:8080/video"
    while True:
        try:
            stream = urllib.request.urlopen(stream_url, timeout=3)
            bytes_data = b''
            while True:
                bytes_data += stream.read(4096)
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                        latest_frame = frame
        except:
            sleep(1)

# ==========================================
# LUỒNG 2: AI QUÉT MẶT NGẦM (KHÔNG LAG)
# ==========================================
def process_frame_thread():
    global latest_frame, face_boxes
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    while True:
        if latest_frame is None:
            sleep(0.05)
            continue
        frame = latest_frame
        scale_ratio = 4.0 
        small_frame = cv2.resize(frame, (int(frame.shape[1] / scale_ratio), int(frame.shape[0] / scale_ratio)))
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=4, minSize=(20, 20))
        temp_face_boxes = []
        for (x, y, w, h) in faces:
            temp_face_boxes.append((int(x * scale_ratio), int(y * scale_ratio), int(w * scale_ratio), int(h * scale_ratio)))
        
        face_boxes = temp_face_boxes
        sleep(0.05)

# ==========================================
# LUỒNG CHÍNH: HIỂN THỊ WEB & CHỤP
# ==========================================
def generate_video():
    global latest_frame, face_boxes
    while True:
        if latest_frame is None:
            sleep(0.05)
            continue
            
        frame = latest_frame.copy()
        
        # ÁP DỤNG FILTER VÀO VIDEO STREAM ĐỂ XEM TRƯỚC!
        frame = apply_filters(frame, face_boxes)
            
        (flag, encodedImage) = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
        if flag:
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')
        sleep(0.02)

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/video_feed")
def video_feed():
    return Response(generate_video(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/capture")
def capture():
    global latest_frame, face_boxes, img_counter
    if latest_frame is not None:
        frame = latest_frame.copy()
        
        # ÁP DỤNG FILTER VÀO ẢNH CHỤP ĐỂ LƯU LẠI
        frame = apply_filters(frame, face_boxes)
            
        img_name = f"photobooth_{img_counter}.png"
        cv2.imwrite(img_name, frame)
        img_counter += 1
        return jsonify(message=f"Đã chụp ảnh có Filter: {img_name}")
    return jsonify(message="Lỗi: Chưa có tín hiệu camera!")

if __name__ == '__main__':
    threading.Thread(target=fetch_stream_thread, daemon=True).start()
    threading.Thread(target=process_frame_thread, daemon=True).start()
    print("🌍 ĐÃ SẴN SÀNG! Mở web tại: http://<IP_CUA_PI>:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
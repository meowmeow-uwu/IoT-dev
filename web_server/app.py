from flask import Flask, render_template, request, jsonify
import RPi.GPIO as GPIO
import time
import board
import adafruit_dht
import threading

app = Flask(__name__)

# --- CẤU HÌNH CẢM BIẾN DHT11 ---
# ĐÃ ĐỔI SANG D17 VÌ D4 BỊ TRÙNG VỚI ĐỘNG CƠ
dhtDevice = adafruit_dht.DHT11(board.D17) 

# --- CẤU HÌNH ĐỘNG CƠ BƯỚC ---
STEPPER_PINS = [9, 25, 10, 4] 
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in STEPPER_PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, False)

HALF_STEP_SEQ = [
    [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0],
    [0,0,1,0], [0,0,1,1], [0,0,0,1], [1,0,0,1]
]

# --- BIẾN TOÀN CỤC CHO THREADING ---
motor_running = False
motor_thread = None

def rotate_stepper(angle, direction):
    """Hàm quay động cơ 1 lần (có thể bị ngắt giữa chừng nếu bấm dừng)"""
    global motor_running
    steps_per_rev = 4096
    steps_needed = int((angle / 360.0) * steps_per_rev)
    
    step_dir = 1 if direction == "thuan" else -1
    step_idx = 0

    for _ in range(steps_needed):
        if not motor_running: # Nếu có lệnh dừng từ web thì ngắt vòng lặp quay
            break
            
        for pin in range(4):
            GPIO.output(STEPPER_PINS[pin], HALF_STEP_SEQ[step_idx][pin])
        
        step_idx += step_dir
        if step_idx >= len(HALF_STEP_SEQ):
            step_idx = 0
        elif step_idx < 0:
            step_idx = len(HALF_STEP_SEQ) - 1
            
        time.sleep(0.002)

    for pin in STEPPER_PINS:
        GPIO.output(pin, False)

def motor_loop(angle, direction):
    """Hàm luồng ngầm: Lặp lại việc quay -> nghỉ 3s"""
    global motor_running
    while motor_running:
        rotate_stepper(angle, direction) # Quay
        
        if not motor_running:
            break
            
        # Nghỉ 3 giây. Thay vì sleep(3) sẽ làm nút Dừng bị trễ, 
        # ta chia nhỏ ra thành 30 lần sleep(0.1s) để check lệnh Dừng liên tục.
        for _ in range(30): 
            if not motor_running:
                break
            time.sleep(0.1)

# --- CÁC ROUTE CỦA FLASK ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/sensor')
def get_sensor_data():
    global motor_running
    
    # THÊM ĐOẠN NÀY: Nếu động cơ đang chạy thì bỏ qua đọc cảm biến
    if motor_running:
        return jsonify({'status': 'busy', 'message': 'Đang bận quay động cơ'})

    try:
        temperature_c = dhtDevice.temperature
        humidity = dhtDevice.humidity
        if temperature_c is not None and humidity is not None:
            return jsonify({'temp': temperature_c, 'hum': humidity, 'status': 'ok'})
    except RuntimeError:
        pass
    return jsonify({'status': 'error', 'message': 'Không thể đọc cảm biến'})

@app.route('/api/motor', methods=['POST'])
def control_motor():
    global motor_running, motor_thread
    data = request.get_json()
    angle = float(data.get('angle', 0))
    direction = data.get('direction', 'thuan')
    
    if angle > 0:
        # Dừng luồng cũ nếu đang chạy
        motor_running = False 
        if motor_thread and motor_thread.is_alive():
            motor_thread.join(timeout=0.5)
            
        # Khởi động luồng mới
        motor_running = True
        motor_thread = threading.Thread(target=motor_loop, args=(angle, direction))
        motor_thread.daemon = True # Cho phép thread tự chết khi thoát chương trình chính
        motor_thread.start()
        
        return jsonify({'status': 'success', 'message': f'Đang lặp: Quay {direction} {angle} độ, nghỉ 3s'})
    
    return jsonify({'status': 'error', 'message': 'Góc quay không hợp lệ'})

@app.route('/api/motor/stop', methods=['POST'])
def stop_motor():
    """Route nhận lệnh dừng động cơ"""
    global motor_running
    motor_running = False
    
    # Tắt chân động cơ ngay lập tức
    for pin in STEPPER_PINS:
        GPIO.output(pin, False)
        
    return jsonify({'status': 'success', 'message': 'Đã dừng động cơ.'})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        pass
    finally:
        motor_running = False
        GPIO.cleanup()
        dhtDevice.exit()
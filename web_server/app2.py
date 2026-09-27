from flask import Flask, render_template, request, jsonify
from gpiozero import OutputDevice
import time
import board
import adafruit_dht
import threading

app = Flask(__name__)

# --- CẢM BIẾN DHT11 ---
dhtDevice = adafruit_dht.DHT11(board.D17)

# --- ĐỘNG CƠ BƯỚC ULN2003 (GPIOZERO) ---
pins = [OutputDevice(9), OutputDevice(25), OutputDevice(10), OutputDevice(4)]

HALF_STEP = [
    [1, 0, 0, 0], [1, 1, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0],
    [0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 0, 1], [1, 0, 0, 1]
]

# --- BIẾN ĐIỀU KHIỂN LUỒNG ---
motor_running = False
target_angle = 0
target_direction = "thuan"
motor_thread = None

def release_pins():
    """Tắt các chân để cuộn dây không bị ngâm điện gây nóng"""
    for pin in pins:
        pin.off()

def rotate_once(angle, direction):
    """Quay ĐỦ toàn bộ số bước của nhịp hiện tại, không cắt ngang"""
    steps = int((angle / 360.0) * 4096)
    seq = HALF_STEP if direction == "thuan" else list(reversed(HALF_STEP))

    for step in range(steps):
        pattern = seq[step % 8]
        for i in range(4):
            pins[i].value = pattern[i]
        time.sleep(0.001)

    release_pins()

def motor_worker():
    """Luồng chạy nền: quay hết nhịp -> nghỉ 0.5s -> kiểm tra lệnh mới"""
    global motor_running, target_angle, target_direction
    while motor_running:
        curr_angle = target_angle
        curr_dir = target_direction
        
        rotate_once(curr_angle, curr_dir)

        # Nghỉ 0.5 giây (kiểm tra nếu có lệnh Dừng thì dừng luôn)
        for _ in range(5):
            if not motor_running:
                break
            time.sleep(0.1)

# --- FLASK ROUTES ---

@app.route('/')
def index():
    return render_template('index2.html')

@app.route('/api/sensor')
def get_sensor_data():
    global motor_running
    if motor_running:
        return jsonify({'status': 'busy'})
    try:
        t, h = dhtDevice.temperature, dhtDevice.humidity
        if t is not None and h is not None:
            return jsonify({'temp': t, 'hum': h, 'status': 'ok'})
    except RuntimeError:
        pass
    return jsonify({'status': 'error'})

@app.route('/api/motor', methods=['POST'])
def control_motor():
    global motor_running, target_angle, target_direction, motor_thread
    data = request.get_json()
    raw_angle = float(data.get('angle', 0))

    if raw_angle != 0:
        # Dương -> Thuận, Âm -> Nghịch
        target_direction = "thuan" if raw_angle > 0 else "nghich"
        target_angle = abs(raw_angle)

        if not motor_running or motor_thread is None or not motor_thread.is_alive():
            motor_running = True
            motor_thread = threading.Thread(target=motor_worker, daemon=True)
            motor_thread.start()

        dir_label = "thuận" if target_direction == "thuan" else "nghịch"
        return jsonify({
            'status': 'success',
            'message': f'Đã cập nhật: Quay {dir_label} {target_angle}°, nghỉ 0.5s lặp lại'
        })

    return jsonify({'status': 'error', 'message': 'Góc quay phải khác 0'})

@app.route('/api/motor/stop', methods=['POST'])
def stop_motor():
    global motor_running
    motor_running = False
    release_pins()
    return jsonify({'status': 'success', 'message': 'Sẽ dừng hẳn sau khi quay nốt nhịp hiện tại.'})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        pass
    finally:
        motor_running = False
        release_pins()
        dhtDevice.exit()
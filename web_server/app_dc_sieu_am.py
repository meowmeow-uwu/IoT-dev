import queue
import threading
import time
from flask import Flask, jsonify, render_template, request
from gpiozero import DistanceSensor, OutputDevice, PWMOutputDevice

app = Flask(__name__)

# --- CẢM BIẾN SIÊU ÂM ---
ultrasonic = DistanceSensor(echo=23, trigger=24, max_distance=3.0)
latest_distance = 0.0


def ultrasonic_worker():
    global latest_distance
    while True:
        try:
            d = ultrasonic.distance * 100
            latest_distance = round(d, 1)
        except Exception:
            pass
        time.sleep(0.1)  # Giảm tải đọc cảm biến xuống 100ms


threading.Thread(target=ultrasonic_worker, daemon=True).start()

# --- ĐỘNG CƠ DC ---
ena = PWMOutputDevice(9, frequency=1000)
in1 = OutputDevice(25)
in2 = OutputDevice(10)

# Queue chứa tối đa 1 lệnh: Lệnh mới luôn đè lệnh cũ chưa kịp chạy
motor_queue = queue.Queue(maxsize=1)
current_direction = 'dung'
current_speed = 0.0


def stop_hardware():
    in1.on()
    in2.on()
    ena.value = 1.0
    time.sleep(0.04)
    ena.value = 0.0
    in1.off()
    in2.off()


def motor_worker():
    """Luồng duy nhất xử lý động cơ, loại bỏ hoàn toàn xung đột lock."""
    global current_direction, current_speed

    while True:
        target_dir, speed_pct = motor_queue.get()
        target_speed = max(0.0, min(100.0, float(speed_pct))) / 100.0

        # Lệnh dừng
        if target_dir == 'dung' or target_speed == 0:
            stop_hardware()
            current_direction = 'dung'
            current_speed = 0.0
            motor_queue.task_done()
            continue

        # Đảo chiều
        if current_direction in ['thuan', 'nghich'] and target_dir != current_direction:
            stop_hardware()
            time.sleep(0.06)

        # Đặt chiều quay
        if target_dir == 'thuan':
            in1.on()
            in2.off()
        elif target_dir == 'nghich':
            in1.off()
            in2.on()

        # Tăng tốc mềm có kiểm tra ngắt (abort check)
        start_speed = current_speed if target_dir == current_direction else 0.0
        steps = 5
        step_delta = (target_speed - start_speed) / steps

        for i in range(1, steps + 1):
            # Nếu có lệnh mới hơn xuất hiện trong hàng đợi, dừng ngay việc tăng tốc
            if not motor_queue.empty():
                break
            ena.value = max(0.0, min(1.0, start_speed + step_delta * i))
            time.sleep(0.02)

        current_direction = target_dir
        current_speed = target_speed
        motor_queue.task_done()


threading.Thread(target=motor_worker, daemon=True).start()


def push_motor_command(direction, speed):
    """Đẩy lệnh vào Queue; nếu đang có lệnh cũ chưa chạy thì xóa bỏ để chạy lệnh mới."""
    try:
        motor_queue.get_nowait()
        motor_queue.task_done()
    except queue.Empty:
        pass
    motor_queue.put((direction, speed))


# --- ROUTES ---


@app.route('/')
def index():
    return render_template('index_dc.html')


@app.route('/api/distance')
def get_distance():
    return jsonify({'distance': latest_distance, 'status': 'ok'})


@app.route('/api/motor', methods=['POST'])
def control_motor():
    data = request.get_json() or {}
    direction = data.get('direction', 'dung')
    speed = data.get('speed', 100)

    push_motor_command(direction, speed)
    return jsonify({'status': 'success', 'message': f'Đã nhận: {direction} ({speed}%)'})


@app.route('/api/motor/stop', methods=['POST'])
def stop_motor():
    push_motor_command('dung', 0)
    return jsonify({'status': 'success', 'message': 'Đã nhận lệnh phanh'})


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    finally:
        stop_hardware()
        ena.close()
        in1.close()
        in2.close()
        ultrasonic.close()
import time
import board
import adafruit_dht
from gpiozero import AngularServo
from gpiozero.pins.lgpio import LGPIOFactory

# Khởi tạo cảm biến
dht_device = adafruit_dht.DHT11(board.D4)

# Khởi tạo Servo
servo = AngularServo(
    18,
    pin_factory=LGPIOFactory(), 
    min_angle=0,
    max_angle=180,
    min_pulse_width=0.0006,  
    max_pulse_width=0.0024,  
)

max_angle = 90
t_read = 0

try:
    servo.angle = 0
    print("Bắt đầu chạy. Nhấn Ctrl+C để thoát.")
    time.sleep(1)

    while True:
        now = time.monotonic()

        # 1. Cập nhật nhiệt độ mỗi 2s
        if now - t_read >= 2.0:
            t_read = now
            try:
                t = dht_device.temperature
                if t is not None:
                    max_angle = 180 if t >= 30 else 90
                    print(f"Nhiệt độ: {t:.1f}°C -> Góc vẫy: {max_angle}°")
            except RuntimeError:
                pass # Bỏ qua lỗi nhịp đập DHT

        # 2. Điều khiển Servo quay một mạch
        servo.angle = max_angle
        # Thời gian chờ cho Servo vật lý quay tới nơi (khoảng 0.5s - 0.8s)
        time.sleep(0.6) 
        
        servo.angle = 0
        time.sleep(0.6) 

except KeyboardInterrupt:
    print("\nĐã dừng chương trình.")
    servo.detach()
    dht_device.exit()
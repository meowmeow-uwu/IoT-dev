import time
import board
import adafruit_dht
from gpiozero import AngularServo
from gpiozero.pins.lgpio import LGPIOFactory

# Khởi tạo thiết bị (Gom cấu hình Servo gọn gàng hơn)
dht_device = adafruit_dht.DHT11(board.D4)
servo = AngularServo(
    18, pin_factory=LGPIOFactory(),
    min_angle=0, max_angle=180,
    min_pulse_width=0.0006, max_pulse_width=0.0024
)

max_angle = 90
t_read = t_servo = 0
servo_state = False  # False: Góc 0, True: Góc max_angle

try:
    servo.angle = 0
    print("Bắt đầu chạy. Nhấn Ctrl+C để thoát.")
    time.sleep(1)

    while True:
        now = time.monotonic()

        # 1. Cập nhật nhiệt độ mỗi 2s (Không dùng sleep)
        if now - t_read >= 2.0:
            t_read = now
            try:
                t = dht_device.temperature
                if t is not None:
                    max_angle = 180 if t >= 30 else 90
                    print(f"Nhiệt độ: {t:.1f}°C -> Góc vẫy: {max_angle}°")
            except RuntimeError:
                pass  # Bỏ qua lỗi đọc của DHT

        # 2. Vẫy Servo bất đồng bộ mỗi 0.6s (Loại bỏ hoàn toàn time.sleep gây nghẽn)
        if now - t_servo >= 0.6:
            t_servo = now
            servo_state = not servo_state
            servo.angle = max_angle if servo_state else 0

        time.sleep(0.01)  # Nghỉ 10ms để giảm tải CPU xuống 0%

except KeyboardInterrupt:
    print("\nĐã dừng chương trình.")
    servo.detach()
    dht_device.exit()

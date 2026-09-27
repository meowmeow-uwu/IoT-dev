import time
import board
import adafruit_dht
from gpiozero import Device, Motor, Button
from gpiozero.pins.lgpio import LGPIOFactory

Device.pin_factory = LGPIOFactory()

# 1. KHỞI TẠO PHẦN CỨNG
dht_device = adafruit_dht.DHT11(board.D17)
button = Button(22, pull_up=True)
motor = Motor(forward=10, backward=11, enable=9)

# 2. BIẾN TRẠNG THÁI VÀ BỘ NHỚ
is_on = False
last_temp = 25.0  # Giả định ban đầu là 25 độ
t_read = 0        # Biến đếm thời gian

def update_motor():
    """Hàm cập nhật motor dựa trên bộ nhớ nhiệt độ (không cần đo lại)"""
    if last_temp >= 30:
        motor.forward(1.0)
        print(f"-> [Motor Đang Chạy] Quay THUẬN (Nhanh)")
    else:
        motor.backward(0.5)
        print(f"-> [Motor Đang Chạy] Quay NGƯỢC (Chậm)")

# 3. HÀM XỬ LÝ NÚT BẤM
def toggle_power():
    global is_on
    is_on = not is_on
    if is_on:
        print("\n-> ĐÃ BẬT HỆ THỐNG")
        update_motor() # Kích hoạt motor CHẠY NGAY LẬP TỨC dựa trên nhiệt độ cũ
    else:
        print("\n-> ĐÃ TẮT HỆ THỐNG")
        motor.stop()

button.when_pressed = toggle_power

# 4. VÒNG LẶP CHÍNH (Non-blocking)
try:
    print("Hệ thống sẵn sàng! Nhấn nút để Bật/Tắt tức thì.")
    
    while True:
        now = time.monotonic()
        
        # Cứ mỗi 2 giây, cảm biến sẽ âm thầm đo và cập nhật nhiệt độ
        if now - t_read >= 2.0:
            t_read = now
            try:
                t = dht_device.temperature
                if t is not None:
                    last_temp = t # Cập nhật bộ nhớ
                    
                    # LUÔN IN NHIỆT ĐỘ LIÊN TỤC DÙ ĐANG BẬT HAY TẮT
                    print(f"🌡 Nhiệt độ hiện tại: {last_temp:.1f}°C")
                    
                    # Nếu hệ thống đang BẬT, tự động cập nhật lại tốc độ theo nhiệt độ mới
                    if is_on:
                        update_motor()
            except RuntimeError:
                pass # Bỏ qua lỗi nhịp đập, hệ thống vẫn chạy bằng nhiệt độ nhớ cũ
                
        # Ngủ một nhịp cực kỳ ngắn (0.05s) để giảm tải CPU mà không làm trễ nút bấm
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nĐã thoát.")
finally:
    motor.stop()
    dht_device.exit()
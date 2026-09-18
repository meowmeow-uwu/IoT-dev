import lgpio
from time import sleep

# Cấu hình chân PIN và Tốc độ (Dùng chuẩn BCM)
SENSOR, BUTTON, EN, IN1, IN2 = 17, 27, 18, 23, 24
FAST, SLOW = 80, 30  # Chu kỳ nhiệm vụ PWM (0 đến 100)
forward = True

# Khởi tạo kết nối GPIO
h = lgpio.gpiochip_open(0)
for p in [SENSOR, BUTTON]: lgpio.gpio_claim_input(h, p)
for p in [EN, IN1, IN2]: lgpio.gpio_claim_output(h, p)

def update_motor():
    """Cập nhật trạng thái động cơ dựa trên cảm biến và hướng quay"""
    line = lgpio.gpio_read(h, SENSOR)
    speed = FAST if line else SLOW
    
    # Điều khiển hướng quay
    lgpio.gpio_write(h, IN1, forward)
    lgpio.gpio_write(h, IN2, not forward)
    # Điều khiển tốc độ bằng PWM trên chân EN (Sửa chính xác thành tx_pwm)
    lgpio.tx_pwm(h, EN, 1000, speed)

def on_button(chip, gpio, level, tick):
    """Hàm xử lý khi có tín hiệu ngắt từ nút bấm"""
    global forward
    # Cạnh lên (level == 1) biểu thị nút được nhấn xuống
    if level == 1:
        forward = not forward
        update_motor()

# Thiết lập chế độ theo dõi trạng thái biên (Alert) cho nút bấm
lgpio.gpio_claim_alert(h, BUTTON, lgpio.BOTH_EDGES)
# Đăng ký hàm ngắt
cb = lgpio.callback(h, BUTTON, lgpio.BOTH_EDGES, on_button)

try:
    print("Hệ thống khởi động thành công. Đang chạy...")
    while True:
        update_motor()  # Liên tục cập nhật tốc độ theo cảm biến dò đường
        
        # In log trạng thái
        line_status = lgpio.gpio_read(h, SENSOR)
        print(f"Hướng: {'TIẾN' if forward else 'LÙI':<4} | Line: {'CÓ' if line_status else 'KHÔNG':<5}")
        
        sleep(0.1)  # Giảm tải cho vòng lặp log, nút bấm vẫn nhận diện ngay lập tức

except KeyboardInterrupt:
    print("\nĐang dừng hệ thống an toàn...")
    cb.cancel()  # Hủy bỏ lắng nghe callback
    lgpio.tx_pwm(h, EN, 0, 0)  # Tắt PWM động cơ an toàn
    lgpio.gpiochip_close(h)  # Giải phóng các chân GPIO

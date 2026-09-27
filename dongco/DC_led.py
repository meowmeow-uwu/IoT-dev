from gpiozero import Motor, Button, LEDBoard
from time import sleep

BTN_PIN = 22
LED_PINS = (4, 25, 8, 7)
ENA = 9
IN1 = 10
IN2 = 11

# Motor tự động băm xung PWM nếu dùng chân enable
motor = Motor(forward=IN1, backward=IN2, enable=ENA)

# Cài đặt hold_time=3.0 để tính là nhấn giữ (3 giây)
button = Button(BTN_PIN, hold_time=3.0, pull_up=True) 
leds = LEDBoard(*LED_PINS)

is_on = False       # Trạng thái bật/tắt động cơ
speed_idx = 0       # Vị trí cấp độ hiện tại (0 -> 3)
was_held = False    # Cờ đánh dấu để phân biệt nhấn giữ và nhấn nhả

SPEEDS = [0.3, 0.5, 0.75, 1.0]
# Tuple ánh xạ trạng thái 4 đèn LED: 1=Sáng, 0=Tắt
LED_STATES = [
    (1, 0, 0, 0),  # 30% -> 1 đèn
    (1, 1, 0, 0),  # 50% -> 2 đèn
    (1, 1, 1, 0),  # 75% -> 3 đèn
    (1, 1, 1, 1)   # 100% -> 4 đèn
]

def update_hardware():
    """Đồng bộ trạng thái phần cứng dựa trên biến is_on và speed_idx"""
    if is_on:
        speed = SPEEDS[speed_idx]
        motor.forward(speed)
        leds.value = LED_STATES[speed_idx]
        print(f"-> Động cơ BẬT | Tốc độ: {speed * 100:.0f}%")
    else:
        motor.stop()
        leds.off()
        print("-> Động cơ TẮT")

def toggle_power():
    """Kích hoạt khi nút được GIỮ ĐỦ 3 GIÂY"""
    global is_on, was_held
    was_held = True       # Bật cờ báo hiệu đây là hành động nhấn giữ
    is_on = not is_on
    update_hardware()

def change_speed():
    """Kích hoạt khi nút ĐƯỢC NHẢ RA"""
    global speed_idx, was_held
    
    # Nếu nút vừa được nhả ra sau khi nhấn giữ 3s -> Bỏ qua, chỉ reset cờ
    if was_held:
        was_held = False
    else:
        # Nếu là nhấn nhả bình thường (short press) -> Chuyển tốc độ
        if is_on:
            speed_idx = (speed_idx + 1) % 4  # Xoay vòng: 0,1,2,3 -> 0,1...
            update_hardware()
        else:
            print("-> Hãy bật động cơ (giữ 3s) trước khi đổi tốc độ.")

button.when_held = toggle_power
button.when_released = change_speed

try:
    print("Hệ thống sẵn sàng!")
    print("- Nhấn giữ 3s: Bật/Tắt động cơ")
    print("- Nhấn nhả (dưới 3s): Đổi tốc độ (30% -> 50% -> 75% -> 100%)")
    
    update_hardware()

    while True:
        sleep(1)
        
except KeyboardInterrupt:
    print("\nĐã dừng chương trình.")
finally:
    motor.stop()
    leds.off()
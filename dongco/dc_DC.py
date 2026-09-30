from gpiozero import Motor, DigitalInputDevice, Button
from time import sleep

# Định nghĩa các chân GPIO (Chân PIN)
SENSOR_PIN = 17
BUTTON_PIN = 27

MOTOR_EN = 9
MOTOR_IN1 = 25
MOTOR_IN2 = 10

# Cấu hình tốc độ
FAST_SPEED = 0.8
SLOW_SPEED = 0.3

# Khởi tạo các thiết bị ngoại vi
sensor = DigitalInputDevice(SENSOR_PIN)
button = Button(BUTTON_PIN, pull_up=False)

motor = Motor(
    forward=MOTOR_IN1,
    backward=MOTOR_IN2,
    enable=MOTOR_EN,
    pwm=True
)

# Biến toàn cục kiểm soát chiều quay
forward = True

# Hàm đảo chiều quay động cơ khi nhấn nút
def reverse_motor():
    global forward
    motor.stop()
    sleep(0.2)
    forward = not forward

# Gán sự kiện nhấn nút cho hàm reverse_motor
button.when_pressed = reverse_motor

# Vòng lặp điều khiển chính
try:
    while True:
        # Kiểm tra trạng thái cảm biến dò đường
        line = sensor.is_active
        
        # Quyết định tốc độ dựa trên cảm biến
        speed = FAST_SPEED if line else SLOW_SPEED
        
        # Xác định chuỗi văn bản hiển thị chiều quay
        direction = "FORWARD" if forward else "BACKWARD"
        
        # Điều khiển động cơ chạy theo chiều hiện tại
        if forward:
            motor.forward(speed)
        else:
            motor.backward(speed)
            
        # In trạng thái hệ thống ra màn hình console
        print(
            f"Direction: {direction:<8} | "
            f"Line: {'YES' if line else 'NO ':<3} | "
            f"Speed: {speed:.2f}"
        )
        
        sleep(0.1)

except KeyboardInterrupt:
    # Dừng động cơ an toàn khi nhấn Ctrl+C
    motor.stop()

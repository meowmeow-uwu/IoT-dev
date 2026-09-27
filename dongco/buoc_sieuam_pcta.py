# file: joystick_stepper.py   (chạy trên Raspberry Pi)
import time
from gpiozero import DistanceSensor
from RpiMotorLib import RpiMotorLib

# ===== CẤU HÌNH =====
ECHO_PIN, TRIG_PIN = 10, 9
STEPPER_PINS = [18, 23, 24, 27]

BASE_CM        = 0.0    # mốc gốc = 0cm (cố định, KHÔNG lấy mẫu)
STEP_CM        = 10.0   # cứ mỗi 10cm lệch = 1 nấc
STEP_ANGLE     = 90     # 1 nấc = 90 độ
STEPS_PER_REV  = 512    # giữ nguyên hệ số của ông (512 nửa-bước = 360°)

MOTOR_WAIT     = 0.001  # delay giữa 2 bước -> nhỏ = nhanh. 0.001 ~ ngưỡng nhanh nhất còn ổn của 28BYJ
MOTOR_INITDELAY = 0.001

sensor  = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN)
mymotor = RpiMotorLib.BYJMotor("MyMotor", "28BYJ")

def quay_dong_co(angle):
    """angle > 0: quay THUẬN | angle < 0: quay NGHỊCH"""
    if angle == 0:
        return
    is_ccwise = angle < 0
    cycles = int((abs(angle) / 360.0) * STEPS_PER_REV)
    if cycles > 0:
        mymotor.motor_run(STEPPER_PINS, MOTOR_WAIT, cycles, is_ccwise, False, "half", MOTOR_INITDELAY)

def doc_khoang_cach_on_dinh(so_mau=5):
    mang = []
    for _ in range(so_mau):
        kc = sensor.distance * 100
        if 2.0 <= kc <= 400.0:
            mang.append(kc)
        time.sleep(0.01)
    if not mang:
        return None
    mang.sort()
    return mang[len(mang) // 2]

# ===== CHƯƠNG TRÌNH CHÍNH =====
current_angle = 0   # góc motor đang giữ so với gốc

print("Joystick siêu âm [ÁNH XẠ TUYỆT ĐỐI] sẵn sàng. Ctrl+C để thoát.")
try:
    while True:
        dist = doc_khoang_cach_on_dinh()
        if dist is None:
            continue

        offset = dist - BASE_CM             # độ lệch khỏi mốc (= dist vì mốc = 0)
        level  = int(offset / STEP_CM)      # 0–10cm->0 | 10–20cm->1 | 20–30cm->2 ...
        target_angle = level * STEP_ANGLE   # góc ĐÍCH ứng với vị trí tay (cố định)

        delta = target_angle - current_angle
        if delta != 0:
            huong = "THUẬN" if delta > 0 else "NGHỊCH"
            print(f"KC:{dist:5.1f}cm | Đích:{target_angle:4d}° | Quay {huong} {delta:+d}° (đang:{current_angle}°)")
            quay_dong_co(delta)             # + thuận, - nghịch -> tự gỡ về gốc khi tay lùi
            current_angle = target_angle
        else:
            tag = "MỐC/RESET" if level == 0 else "GIỮ"
            print(f"KC:{dist:5.1f}cm | Giữ {current_angle:4d}° [{tag}]        ", end="\r")

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nĐã dừng.")
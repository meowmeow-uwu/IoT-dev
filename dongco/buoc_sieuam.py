import time
from gpiozero import DistanceSensor
from RpiMotorLib import RpiMotorLib

# Mở rộng tầm quét tối đa lên 2 mét
sensor = DistanceSensor(echo=23, trigger=24, max_distance=2.0)

STEPPER_PINS = [9, 25, 10, 4]
mymotor = RpiMotorLib.BYJMotor("MyMotor", "28BYJ")

def quay_dong_co(angle, direction="thuan"):
    cycles = int((angle / 360.0) * 512)
    if cycles > 0:
        is_ccwise = True if direction == "nghich" else False
        # GIẢM stepdelay từ 0.003 xuống 0.0012 và GIẢM initdelay từ 0.05 xuống 0.001 để tăng tốc
        mymotor.motor_run(STEPPER_PINS, 0.0012, cycles, is_ccwise, False, "half", 0.001)

def doc_khoang_cach_on_dinh(so_mau=3):
    """Giảm số mẫu xuống 3 để phản xạ nhanh hơn khi ở cự ly xa"""
    mang_gia_tri = []
    for _ in range(so_mau):
        kc = sensor.distance * 100
        if 2.0 <= kc <= 200.0:
            mang_gia_tri.append(kc)
        time.sleep(0.01) # Giảm thời gian trễ giữa các mẫu để đọc nhanh hơn
    if not mang_gia_tri:
        return None
    mang_gia_tri.sort()
    return mang_gia_tri[len(mang_gia_tri) // 2]

def xac_dinh_muc_linh_hoat(distance):
    """Tự động tính mức và góc không giới hạn trần 270 độ"""
    if distance < 10.0:
        return 0, 0
    level = int(distance // 10)
    angle = level * 90
    return level, angle

current_dir = "thuan"
prev_level = 0

print("Hệ thống mở rộng sẵn sàng...")

try:
    while True:
        dist = doc_khoang_cach_on_dinh()
        if dist is None:
            print("Đang tìm tay / ngoài tầm quét...             ", end="\r")
            time.sleep(0.05)
            continue

        level, angle = xac_dinh_muc_linh_hoat(dist)

        if level > prev_level:
            current_dir = "thuan"
            prev_level = level
        elif level < prev_level:
            current_dir = "nghich"
            prev_level = level

        if level == 0:
            print(f"KC: {dist:.1f}cm | Mức 0 -> Đứng yên               ", end="\r")
            time.sleep(0.05)
        else:
            print(f"\nKC: {dist:.1f}cm | Mức {level} | T = {angle}° | Chiều: {current_dir.upper()}")
            quay_dong_co(angle, current_dir)
            # GIẢM thời gian nghỉ sau khi quay từ 0.5s xuống 0.1s để vòng lặp quét liên tục
            time.sleep(0.1)

except KeyboardInterrupt:
    print("\nĐã dừng.")

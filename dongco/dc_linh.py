import time
from gpiozero import DistanceSensor
from RpiMotorLib import RpiMotorLib

# 1. KHỞI TẠO CẢM BIẾN & ĐỘNG CƠ
sensor = DistanceSensor(echo=10, trigger=9)
STEPPER_PINS = [18, 23, 24, 27]
mymotor = RpiMotorLib.BYJMotor("MyMotor", "28BYJ")

def quay_dong_co(angle):
    is_ccwise = True if angle < 0 else False
    # 28BYJ-48 ở chế độ half-step cần 512 chu kỳ (4096 bước) cho 360 độ
    cycles = int((abs(angle) / 360.0) * 512)
    if cycles > 0:
        mymotor.motor_run(STEPPER_PINS, 0.002, cycles, is_ccwise, False, "half", 0.05)

def doc_khoang_cach_on_dinh(so_mau=5):
    mang_gia_tri = []
    for _ in range(so_mau):
        kc = sensor.distance * 100
        if 2.0 <= kc <= 400.0:
            mang_gia_tri.append(kc)
        time.sleep(0.01)
    
    if not mang_gia_tri:
        return None
    mang_gia_tri.sort()
    return mang_gia_tri[len(mang_gia_tri) // 2]

# 2. CHƯƠNG TRÌNH CHÍNH
print("Hệ thống điều khiển góc theo khoảng cách sẵn sàng. Nhấn Ctrl+C để thoát...")

# Đọc mẫu ban đầu để xác định nấc khởi điểm
kc_dau = None
while kc_dau is None:
    kc_dau = doc_khoang_cach_on_dinh()

# Mỗi nấc tương ứng với 10cm (VD: 20-29cm là nấc 2, 30-39cm là nấc 3)
last_step = int(kc_dau // 10)
tong_goc = 0
print(f"Khoảng cách ban đầu: {kc_dau:.1f} cm (Nấc mốc: {last_step} - {last_step * 10}cm)")

try:
    while True:
        dist = doc_khoang_cach_on_dinh()
        if dist is None:
            continue

        # Xác định nấc hiện tại
        current_step = int(dist // 10)
        delta_step = current_step - last_step

        # Nếu thay đổi từ 1 nấc (>= 10cm) trở lên
        if delta_step != 0:
            angle = delta_step * 90
            tong_goc += angle
            
            if delta_step > 0:
                print(f"-> TĂNG {delta_step * 10}cm (KC: {dist:.1f}cm) | QUAY THUẬN {angle}° | Góc hiện tại: {tong_goc}°")
            else:
                print(f"-> GIẢM {abs(delta_step) * 10}cm (KC: {dist:.1f}cm) | QUAY NGHỊCH {angle}° | Góc hiện tại: {tong_goc}°")
            
            quay_dong_co(angle)
            last_step = current_step  # Cập nhật lại mốc nấc
        else:
            print(f"Khoảng cách: {dist:.1f}cm (Mốc: {last_step * 10}cm | Góc: {tong_goc}°)    ", end="\r")

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n\nĐã dừng chương trình.")
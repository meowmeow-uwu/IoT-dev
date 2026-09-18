import time
import board
import adafruit_dht
from RpiMotorLib import RpiMotorLib

# 1. Khởi tạo Cảm biến & Động cơ
dht_device = adafruit_dht.DHT11(board.D17)
STEPPER_PINS = [9, 25, 10, 4] 
mymotor = RpiMotorLib.BYJMotor("MyMotor", "28BYJ")

def quay_dong_co(angle, direction="thuan"):
    """
    Hàm quay động cơ với góc dynamic từ 0 - 360 độ.
    - angle: Góc quay (0-360)
    - direction: "thuan" hoặc "nghich"
    """
    # Ép giới hạn góc không được vượt quá 360 và không được nhỏ hơn 0
    angle = max(0, min(360, angle))
    
    # CÔNG THỨC TÍNH SỐ CHU KỲ TỰ ĐỘNG
    cycles = int((angle / 360.0) * 512)
    
    if cycles > 0:
        # Xác định chiều quay: True = Ngược chiều (ccwise), False = Thuận chiều
        is_ccwise = True if direction == "nghich" else False
        
        # Thực thi quay
        mymotor.motor_run(STEPPER_PINS, 0.002, cycles, is_ccwise, False, "half", 0.05)


print("Đang giám sát nhiệt độ. Nhấn Ctrl+C để thoát...")

try:
    while True:
        try:
            t = dht_device.temperature
            h = dht_device.humidity
            
            if t is not None:
                print(f"Nhiệt độ: {t:.1f}°C | Độ ẩm: {h:.1f}%")
                
                if t >= 30:
                    print("-> Nhiệt >= 30°C: Quay 180 độ ngược chiều")
                    quay_dong_co(180, "nghich")
                else:
                    print("-> Nhiệt < 30°C: Quay 90 độ thuận chiều")
                    quay_dong_co(90, "thuan")
                
                print("-> Đã quay xong, nghỉ 2s...")
                
        except RuntimeError as e:
            print("Loi cam bien", e)

        time.sleep(2.0)

except KeyboardInterrupt:
    print("\nĐã dừng chương trình.")
finally:
    dht_device.exit()
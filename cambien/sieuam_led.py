from gpiozero import DistanceSensor, PWMLED
from time import sleep


# =========================
# 1. KHAI BÁO PHẦN CỨNG
# =========================

sensor = DistanceSensor(
    echo=24,
    trigger=23,
    max_distance=4
)

led = PWMLED(17)


# =========================
# 2. THAM SỐ BÀI TOÁN
# =========================

MIN_DISTANCE = 5      # cm: gần nhất -> sáng 100%
MAX_DISTANCE = 50     # cm: từ 50 cm trở lên -> tắt


# =========================
# 3. CHƯƠNG TRÌNH CHÍNH
# =========================

try:
    while True:

        # Đọc khoảng cách từ cảm biến
        distance = sensor.distance * 100

        # -------------------------
        # Tính độ sáng LED
        # -------------------------

        if distance >= MAX_DISTANCE:
            # >= 50 cm -> tắt
            brightness = 0

        elif distance <= MIN_DISTANCE:
            # <= 5 cm -> sáng tối đa
            brightness = 1

        else:
            # 5 -> 50 cm
            # càng xa -> càng mờ
            brightness = (
                (MAX_DISTANCE - distance)
                / (MAX_DISTANCE - MIN_DISTANCE)
            )

        # Gán độ sáng cho LED
        led.value = brightness

        # Hiển thị kết quả
        print(
            f"Khoảng cách: {distance:.2f} cm | "
            f"Độ sáng: {brightness * 100:.1f}%"
        )

        sleep(0.1)


except KeyboardInterrupt:
    print("\nĐã dừng chương trình.")
    led.off()

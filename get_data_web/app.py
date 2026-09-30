import datetime
import os
import sys
import threading
import time
from dotenv import load_dotenv
from gpiozero import LED, Motor
from weather import get_weather

load_dotenv()

# Chu kỳ cập nhật và in thông tin (giây)
# Gói OpenWeather miễn phí cho phép tối đa 60 lượt/phút; 10s là khoảng thời gian lý tưởng
UPDATE_INTERVAL_SEC = 2

# Khởi tạo phần cứng (Motor qua cầu H: L298N/L9110S..., LED qua điện trở)
led = LED(18)
motor = Motor(forward=23, backward=24, pwm=True)

# Biến dùng chung giữa 2 luồng
shared_city = ""
city_lock = threading.Lock()
stop_event = threading.Event()
reload_event = threading.Event()

current_motor_direction = None  # Theo dõi chiều quay để chống giật cơ khí


def control_motor(temperature):
    """Điều khiển tốc độ, chiều quay động cơ và đệm dừng chống giật khi đổi chiều."""
    global current_motor_direction

    if temperature >= 30.0:
        target_direction = "forward"
        speed = 1.0  # Quay thuận, tốc độ nhanh (100%)
        label = "THUẬN - Nhanh (100%)"
    else:
        target_direction = "backward"
        speed = 0.45  # Quay nghịch, tốc độ chậm (45%)
        label = "NGHỊCH - Chậm (45%)"

    # Nếu đổi chiều quay: dừng 0.3s để triệt tiêu quán tính và xung dòng
    if current_motor_direction is not None and current_motor_direction != target_direction:
        motor.stop()
        time.sleep(0.3)

    if target_direction == "forward":
        motor.forward(speed)
    else:
        motor.backward(speed)

    current_motor_direction = target_direction
    return label


def control_led(rain_prob):
    """Bật đèn LED khi khả năng mưa trên 70%."""
    if rain_prob > 70.0:
        led.on()
        return "BẬT (>70%)"
    else:
        led.off()
        return "TẮT (<=70%)"


def monitor_worker(api_key):
    """Luồng chạy ngầm: liên tục gọi API, điều khiển thiết bị và in kết quả ra màn hình."""
    while not stop_event.is_set():
        with city_lock:
            city = shared_city

        if city:
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            try:
                name, temp, humidity, rain_prob = get_weather(city, api_key)
                motor_status = control_motor(temp)
                led_status = control_led(rain_prob)

                # In nhật ký trạng thái liên tục
                print(
                    f"[{now_str}] {name:15} | {temp:4.1f}°C | Ẩm: {humidity:2}% | "
                    f"Mưa: {rain_prob:2.0f}% (LED {led_status}) | Động cơ: {motor_status}"
                )
            except ValueError as err:
                print(f"[{now_str}] Lỗi: {err}")

        # Nghỉ theo chu kỳ hoặc thức dậy ngay lập tức nếu người dùng đổi thành phố
        reload_event.wait(timeout=UPDATE_INTERVAL_SEC)
        reload_event.clear()


def main():
    global shared_city

    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        print("Lỗi: Chưa thiết lập OPENWEATHER_API_KEY trong file .env")
        sys.exit(1)

    # 1. Nhập thành phố theo dõi đầu tiên
    initial_city = ""
    while not initial_city:
        initial_city = input("Nhập thành phố cần theo dõi ban đầu: ").strip()

    with city_lock:
        shared_city = initial_city

    print(f"\n>>> Bắt đầu theo dõi '{initial_city}'. Cập nhật mỗi {UPDATE_INTERVAL_SEC} giây.")
    print(">>> Bạn có thể gõ tên thành phố khác và bấm Enter bất cứ lúc nào (hoặc gõ 'q' để thoát):\n")

    # 2. Khởi chạy luồng in và điều khiển ngầm
    worker = threading.Thread(target=monitor_worker, args=(api_key,), daemon=True)
    worker.start()

    # 3. Luồng chính chờ nhận dữ liệu bàn phím mà không chặn luồng in
    try:
        while True:
            new_city = input().strip()

            if not new_city:
                continue

            if new_city.lower() == "q":
                print("\nĐang dừng hệ thống...")
                break

            with city_lock:
                shared_city = new_city

            print(f"\n---> Đã chuyển sang theo dõi: {new_city}")
            # Đánh thức luồng worker để cập nhật thành phố mới ngay lập tức
            reload_event.set()

    except KeyboardInterrupt:
        print("\nNhận tín hiệu ngắt (Ctrl+C)...")
    finally:
        # Tắt thiết bị an toàn khi thoát
        stop_event.set()
        reload_event.set()
        worker.join(timeout=2.0)

        motor.stop()
        motor.close()
        led.off()
        led.close()
        print("Đã ngắt kết nối động cơ, tắt đèn LED và kết thúc chương trình.")


if __name__ == "__main__":
    main()
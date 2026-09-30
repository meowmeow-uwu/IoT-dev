import threading
import time
from gpiozero import LED, Motor
import requests

# --- CẤU HÌNH THIẾT BỊ ---
# IN1 = 25, IN2 = 10, ENA = 9, LED = 18
motor = Motor(forward=25, backward=10, enable=9, pwm=True)
led = LED(18)

# --- CẤU HÌNH API ---
API_KEY = "545c52540c8af18b10c6bff571e924e8"
UPDATE_INTERVAL = 5

current_city = None
running = True
lock = threading.Lock()


def get_weather(city_name):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={API_KEY}&units=metric&lang=vi"
    try:
        response = requests.get(url, timeout=8)
        data = response.json()
        if response.status_code != 200 or str(data.get("cod")) != "200":
            return None

        current = data["list"][0]
        return {
            "city": data["city"]["name"],
            "temp": current["main"]["temp"],
            "humidity": current["main"]["humidity"],
            "desc": current["weather"][0]["description"],
            "pop": current.get("pop", 0) * 100,
        }
    except Exception:
        return None


def control_devices(temp, pop):
    # --- ĐIỀU CHỈNH TỐC ĐỘ TẠI ĐÂY ---
    # >= 30: Quay thuận - Tối đa 100% (1.0)
    # < 30 : Quay nghịch - Chậm vừa đủ lực 65% (0.65) để không bị đứng/đơ
    if temp >= 30:
        motor.forward(speed=1.0)
        motor_status = "Quay THUẬN - Nhanh (100%)"
    else:
        # Nếu động cơ của bạn tải nặng vẫn hơi khựng, có thể tăng lên 0.70 (70%)
        motor.backward(speed=0.65)
        motor_status = "Quay NGHỊCH - Chậm (65%)"

    # Đèn sáng khi dự báo mưa > 70%
    if pop > 70:
        led.on()
        led_status = "BẬT (Mưa > 70%)"
    else:
        led.off()
        led_status = "TẮT (Mưa <= 70%)"

    return motor_status, led_status


def weather_worker():
    global running, current_city

    last_time = 0
    active_city = None

    while running:
        with lock:
            target_city = current_city

        if target_city:
            if (
                target_city != active_city
                or (time.time() - last_time) >= UPDATE_INTERVAL
            ):
                active_city = target_city
                last_time = time.time()

                weather = get_weather(active_city)
                if weather:
                    m_stat, l_stat = control_devices(
                        weather["temp"], weather["pop"]
                    )
                    print(
                        f"\n[{time.strftime('%H:%M:%S')}] Cập nhật cho: {weather['city']}"
                    )
                    print(
                        f"  -> Thời tiết: {weather['desc'].capitalize()} | Nhiệt độ: {weather['temp']}°C | Tỉ lệ mưa: {weather['pop']:.0f}%"
                    )
                    print(f"  -> Động cơ: {m_stat} | LED: {l_stat}")
                    print("Nhập tên thành phố khác (hoặc 'exit'): ", end="", flush=True)
                else:
                    print(
                        f"\n[!] Không lấy được dữ liệu cho '{active_city}'. Hãy kiểm tra lại tên."
                    )
                    print("Nhập tên thành phố khác (hoặc 'exit'): ", end="", flush=True)

        time.sleep(0.5)


def main():
    global running, current_city

    print("=" * 50)
    print(" HỆ THỐNG GIÁM SÁT THỜI TIẾT TỰ ĐỘNG")
    print("=" * 50)

    worker_thread = threading.Thread(target=weather_worker, daemon=True)
    worker_thread.start()

    try:
        while True:
            city_input = input("Nhập tên thành phố (hoặc 'exit'): ").strip()
            if not city_input:
                continue
            if city_input.lower() == "exit":
                break

            with lock:
                current_city = city_input

    except KeyboardInterrupt:
        pass
    finally:
        running = False
        motor.stop()
        motor.close()
        led.close()
        print("\nĐã tắt thiết bị và thoát an toàn.")


if __name__ == "__main__":
    main()
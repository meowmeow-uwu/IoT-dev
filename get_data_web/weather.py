import requests


def get_json(url, params):
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as error:
        if error.response is not None and error.response.status_code == 401:
            raise ValueError("API key OpenWeather không hợp lệ hoặc chưa được kích hoạt.") from None
        raise ValueError("Không thể lấy dữ liệu từ OpenWeather.") from None
    return response.json()


def get_weather(city, api_key):
    # 1. Định vị tọa độ thành phố
    locations = get_json(
        "https://api.openweathermap.org/geo/1.0/direct",
        {"q": city, "limit": 1, "appid": api_key},
    )
    if not locations:
        raise ValueError(f"Không tìm thấy thành phố '{city}'.")

    location = locations[0]
    lat, lon = location["lat"], location["lon"]

    # 2. Lấy thời tiết hiện tại (nhiệt độ, độ ẩm)
    weather = get_json(
        "https://api.openweathermap.org/data/2.5/weather",
        {
            "lat": lat,
            "lon": lon,
            "units": "metric",
            "appid": api_key,
        },
    )
    current = weather["main"]
    temp = current["temp"]
    humidity = current["humidity"]

    # 3. Lấy dự báo xác suất mưa (pop) từ endpoint forecast (3h gần nhất)
    rain_prob = 0.0
    try:
        forecast = get_json(
            "https://api.openweathermap.org/data/2.5/forecast",
            {
                "lat": lat,
                "lon": lon,
                "units": "metric",
                "appid": api_key,
                "cnt": 1,  # Lấy mốc dự báo kế tiếp gần nhất
            },
        )
        if forecast.get("list"):
            # pop có giá trị từ 0.0 (0%) đến 1.0 (100%)
            rain_prob = forecast["list"][0].get("pop", 0.0) * 100
    except Exception:
        rain_prob = 0.0

    return location["name"], temp, humidity, rain_prob
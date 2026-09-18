import RPi.GPIO as GPIO
import time

# Chân BCM 17, 18, 27, 22
STEPPER_PINS = [9, 25, 10, 4]

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in STEPPER_PINS:
    GPIO.setup(pin, GPIO.OUT)

# Chuỗi xung quay
SEQ = [
  [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0],
  [0,0,1,0], [0,0,1,1], [0,0,0,1], [1,0,0,1]
]

try:
    print("Động cơ đang quay... Nhấn Ctrl+C để dừng.")
    while True:
        for step in SEQ:
            for pin in range(4):
                GPIO.output(STEPPER_PINS[pin], step[pin])
            # Nếu động cơ chỉ rung mà không quay, thử tăng số 0.002 lên 0.005
            time.sleep(0.002) 
            
except KeyboardInterrupt:
    GPIO.cleanup()
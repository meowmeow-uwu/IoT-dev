import time
from gpiozero import Motor

motor = Motor(forward=23, backward=24, enable=18)

try:
    print("--- BẮT ĐẦU TEST ĐỘNG CƠ DC ---")

    while True:
        print("1. Quay tới (100% công suất) trong 3 giây...")
        motor.forward(speed=1.0)
        time.sleep(3)

        print("2. Dừng 1 giây...")
        motor.stop()
        time.sleep(1)

        print("3. Quay lùi (100% công suất) trong 3 giây...")
        motor.backward(speed=1.0)
        time.sleep(3)

        print("4. Dừng 1 giây...")
        motor.stop()
        time.sleep(1)

        print("5. Test điều tốc: Quay tới với 50% công suất trong 3 giây...")
        motor.forward(speed=0.5)
        time.sleep(3)

        print("6. Dừng 2 giây trước khi lặp lại...")
        motor.stop()
        time.sleep(2)

except KeyboardInterrupt:
    print("\nĐã dừng chương trình kiểm tra.")
    motor.stop()

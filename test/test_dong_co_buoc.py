
from gpiozero import OutputDevice
from time import sleep

# Chân GPIO nối với ULN2003
IN1 = OutputDevice(9)
IN2 = OutputDevice(25)
IN3 = OutputDevice(10)
IN4 = OutputDevice(4)

# Chuỗi điều khiển động cơ
sequence = [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1]
]


def set_step(step):
    IN1.value = step[0]
    IN2.value = step[1]
    IN3.value = step[2]
    IN4.value = step[3]


def rotate(steps, direction=1):

    if direction == 1:
        steps_sequence = sequence
    else:
        steps_sequence = list(reversed(sequence))

    for _ in range(steps):
        for step in steps_sequence:
            set_step(step)
            sleep(0.003)


try:
    print("=== TEST DONG CO BUOC ===")

    print("Quay thuan...")
    rotate(512, direction=1)

    sleep(1)

    print("Quay nguoc...")
    rotate(512, direction=-1)

    print("Hoan thanh!")

finally:
    set_step([0, 0, 0, 0])

    IN1.close()
    IN2.close()
    IN3.close()
    IN4.close()

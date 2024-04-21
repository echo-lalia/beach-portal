from machine import Pin
import time

button = Pin(38, Pin.IN)

while True:
    print(button.value())
    time.sleep(0.1)
from machine import Pin
import time

# PicoWのデフォルトLEDを設定
led = Pin("LED", Pin.OUT)

while True:
    led.value(1) # 点灯
    time.sleep(1)
    led.value(0) # 消灯
    time.sleep(1)

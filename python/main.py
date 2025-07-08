from machine import PWM, Pin
import utime

class Robot:
    def __init__(self):
        self.IN1 = Pin(1, Pin.OUT)
        self.IN2 = Pin(2, Pin.OUT)
        self.IN3 = Pin(3, Pin.OUT)
        self.IN4 = Pin(4, Pin.OUT)
    def forward(self):
        self.IN1.value(1)
        self.IN2.value(0)
        self.IN3.value(1)
        self.IN4.value(0)
    def right(self):
        self.IN1.value(1)
        self.IN2.value(1)
        self.IN3.value(1)
        self.IN4.value(0)
    def left(self):
        self.IN1.value(1)
        self.IN2.value(0)
        self.IN3.value(1)
        self.IN4.value(1)
    def back(self):
        self.IN1.value(0)
        self.IN2.value(1)
        self.IN3.value(0)
        self.IN4.value(1)
    def stop(self):
        self.IN1.value(1)
        self.IN2.value(1)
        self.IN3.value(1)
        self.IN4.value(1)
    def release(self):
        self.IN1.value(0)
        self.IN2.value(0)
        self.IN3.value(0)
        self.IN4.value(0)

class Photo_sensor:
    def __init__(self):
        self.sensor_1 = Pin(6, Pin.IN)

    def read_sensor(self):
        return self.sensor_1.value()

robot = Robot()
sensor = Photo_sensor()
utime.sleep(1)

while True:
    if sensor.read_sensor() == 0:
        robot.left()
    else:
        robot.right()

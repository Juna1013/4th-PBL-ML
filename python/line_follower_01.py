from machine import PWM, Pin
import utime

# モーター制御のためのクラス
class Robot:
    # クラスが初期化されるときに呼び出される
    def __init__(self):
        # 4つのPinのオブジェクトの初期化
        # GPIOピンを出力モードとして設定
        self.IN1 = Pin(1, Pin.OUT)
        self.IN2 = Pin(2, Pin.OUT)
        self.IN3 = Pin(3, Pin.OUT)
        self.IN4 = Pin(4, Pin.OUT)
    # 前進
    def forward(self):
        self.IN1.value(1)
        self.IN2.value(0)
        self.IN3.value(1)
        self.IN4.value(0)
    # 右折
    def right(self):
        self.IN1.value(1)
        self.IN2.value(1)
        self.IN3.value(1)
        self.IN4.value(0)
    # 左折
    def left(self):
        self.IN1.value(1)
        self.IN2.value(0)
        self.IN3.value(1)
        self.IN4.value(1)
    # 後退
    def back(self):
        self.IN1.value(0)
        self.IN2.value(1)
        self.IN3.value(0)
        self.IN4.value(1)
    # 停止
    def stop(self):
        self.IN1.value(1)
        self.IN2.value(1)
        self.IN3.value(1)
        self.IN4.value(1)
    # モーター駆動の解放（自由に回転できる状態）
    def release(self):
        self.IN1.value(0)
        self.IN2.value(0)
        self.IN3.value(0)
        self.IN4.value(0)

# ライントレースセンサーから入力を読み取る
class Photo_sensor:
    # Pinオブジェクトの初期化
    def __init__(self):
        self.sensor_1 = Pin(6, Pin.IN)

    # センサー値の読み取り
    def read_sensor(self):
        # デジタル値の読み取り
        return self.sensor_1.value()

# クラスのオブジェクトの作成
robot = Robot()
# Photo_sensorクラスのインスタンスを作成
sensor = Photo_sensor()
# プログラム開始後、1秒間待機
utime.sleep(1)

# ライントレース
while True:
    if sensor.read_sensor() == 0:
        robot.left()
    else:
        robot.right()

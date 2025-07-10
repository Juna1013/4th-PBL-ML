'''
# line_follwer_01.pyの改善点

## 単一センサーでのライントレース
- 1つのセンサーでは蛇行運転になる
- ラインから外れたことを検知する「戻る」制御にはなるものの、ラインの中心を追従することができない

## モーター制御の明確化
- right()やleft()メソッドでのINピンのHIGH/LOW設定がどのモーターで動作するのか直感的ではない
- 以下の修正が望ましい
 - コメントを追加する
 - より分かりやすい関数名を使用する
 - モータードライバーの挙動に合わせて調整する

## 速度制御の欠如
- モーター速度をPWMで制御するコードがない
- 常に最大速度で動くため、調整が難しく急な動きになる
- machine.PWMがインポートされているにも関わらず使われていない

## マジックナンバーの排除
- GPIOピン番号やセンサーの閾値が直接コードに書かれている
- 定数として定義することでコードの可読性と保守性が向上する

## デバッグ出力の追加
- センサーの状態やモーターの指示がどうなっているかをラルタイムで確認

# line_follower_02.pyでの修正点

## PWMによる速度制御の導入
- Robotクラスにset_speedメソッドを追加し、PWMを使ってモーター速度を制御できるようにした

## 旋回ロジックの修正
- センサーが中央からずれたときに左右のモーターを調整して旋回するように修正

## 定数の定義
- ピン番号、速度、センサー閾値を定数として定義

## デバッグ出力の追加
- シリアルポートに現在のセンサー状態とモーター指示を出力

'''
from machine import Pin, PWM
import utime

# モーター制御ピン
# 左モーター
MOTOR_LEFT_IN1_PIN = 1
MOTOR_LEFT_IN2_PIN = 2
MOTOR_LEFT_PWM_PIN = 7
# 右モーター
MOTOR_RIHHT_IN3_PIN = 3
MOTOR_RIGHT_IN4_PIN = 4
MOTOR_RIGHT_PWM_PIN = 8

# ラインセンサーピン
SENSOR_CENTER_PIN = 6

# 速度設定
BASE_SPEED = 50000
TURN_ADJUST = 20000

# センサー閾値
LINE_DETECTION_VALUE = 0

PWM_FREQ = 1000

# クラス定義
class Robot:
    def __init__(self):
        # モーター方向制御ピンの初期化
        self.in1 = Pin(MOTOR_LEFT_IN1_PIN, Pin.OUT)
        self.in2 = Pin(MOTOR_LEFT_IN2_PIN, Pin.OUT)
        self.in3 = Pin(MOTOR_RIGHT_IN3_PIN, Pin.OUT)
        self.in4 = Pin(MOTOR_RIGHT_IN4_PIN, Pin.OUT)

        # PWMピンの初期化
        self.pwm_left = PWM(Pin(MOTOR_LEFT_PWM_PIN))
        self.pwm_right = PWM(Pin(MOTOR_RIGHT_PWM_PIN))
        self.pwm_left.freq(PWM_FREQ)
        self.pwm_right.freq(PWM_FREQ)

        #初期状態は停止
        self.stop()
    def _set_motor_direction(self, motor_side, direction):

    def set_speed(self, left_speed, right_speed):

    def forward(self, speed=BASE_SPEED):

    def turn_right(self, base_speed=BASE_SPEED, adjust=TURN_ADJUST):

    def turn_left(self, base_speed=BASE_SPEED, adjust=TURN_ADJUST):

    def back(self, speed=BASE_SPEED):

    def stop(self):

    def release(self):

class Photo_sensor:
    def __init__(self):

    def read_center_sensor(self):

robot = Robot()
sensor = Photo_sensor()
utime.sleep(1)

try:

except KeyboardInterrupt:

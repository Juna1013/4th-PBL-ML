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
    """
    モーターの方向を設定するヘルパー関数
    motor_side: 'left' or 'right'
    direction: 'forward', 'backward', 'stop_brake', 'stop_free'
    """
    if motor_side == 'left':
        if direction == 'forward':
            self.in1.value(1)
            self.in2.value(0)
        elif direction == 'backward':
            self.in1.value(0)
            self.in2.value(1)
        elif direction == 'stop_brake':
            self.in1.value(1)
            self.in2.value(1)
        elif direction == 'stop_free':
            self.in1.value(0)
            self.in2.value(0)
    elif motor_side == 'right':
        if direction == 'forward':
            self.in3.value(1)
            self.in4.value(0)
        elif direction == 'backward':
            self.in3.value(0)
            self.in4.value(1)
        elif direction == 'stop_brake':
            self.in3.value(1)
            self.in4.value(1)
        elif directon == 'stop_free':
            self.in3.value(0)
            self.in4.value(0)

    def set_speed(self, left_speed, right_speed):
        """
        左右のモーター速度を設定
        speed: 0（停止）から65535（最大）の値
        方向はforwardメソッドで設定済みを前提
        """
        # 速度範囲を0-65535に制限
        left_speed = max(0, min(65535, left_speed))
        right_speed = max(0, min(65535, right_speed))

        self.pwm_left.duty_u16(left_speed)
        self.pwm_right.duty_u16(right_speed)

    def forward(self, speed=BASE_SPEED):
        self._set_motor_direction('left', 'forward')
        self._set_motor_direction('right', 'forward')
        self.set_speed(speed, speed)

    def turn_right(self, base_speed=BASE_SPEED, adjust=TURN_ADJUST):
        # 左に旋回（右モーター遅め、左モーター遅め/停止）
        self._set_motor_direction('left', 'forward')
        self._set_motor_direction('right', 'forward')
        self.set_speed(base_speed - adjust, base_speed + adjust)

    def turn_left(self, base_speed=BASE_SPEED, adjust=TURN_ADJUST):
        # 左に旋回（右モーター速め、左モーター遅め/停止）
        self._set_motor_direction('left', 'forward') 
        self._set_motor_direction('right', 'forward')
        self.set_speed(base_speed - adjust, base_speed + adjust)

    def back(self, speed=BASE_SPEED):
        self._set_motor_direction('left', 'backward')
        self._set_motor_direction('right', 'backward')
        self.set_speed(speed, speed)

    def stop(self):
        # ブレーキをかけて停止
        self._set_motor_direction('left', 'stop_brake')
        self._set_motor_direction('right', 'stop_brake')
        self.set_speed(0, 0)

    def release(self):
    # モーターをフリーにする
        self._set_motor_direction('left', 'stop_free')
        self._set_motor_direction('right', 'stop_free')
        self.set_speed(0, 0) 


class Photo_sensor:
    def __init__(self):
        self.sensor_center = Pin(SENSOR_CENTER_PIN, Pin.IN)
        # 複数センサーを使用する場合の例
        # self.sensor_left = Pin(SENSOR_LEFT_PIN, Pin.IN)
        # self.sensor_right = Pin(SENSOR_RIGHT_PIN, Pin.IN)

    def read_center_sensor(self):
        return self.sensor_center.value()
    # 複数センサーを使用する場合の例
    # def read_all_sensors(self):
    #     return {
    #         'left': self.sensor_left.value(),
    #         'center': self.sensor_center.value(),
    #         'right': self.sensor_right.value()
    #     }

robot = Robot()
sensor = Photo_sensor()
utime.sleep(1)

try:
    while True:
        current_sensor_value = sensor.read_center_sensor()

        print(f"センサー値: {current_sensor_value}", end=" -> ")

        if current_sensor_value == LINE_DETECTED_VALUE:
            # ラインを検知している場合（中央のラインに乗っている）
            # 基本的に直進
            robot.forward(BASE_SPEED)
            print("直進")
        else:
            # ラインを検知していない場合（ラインから外れた、白い床）
            # このロジックは、センサーがラインの「どちら側」にあるかによって変わる
            # 例: センサーがラインの左側をなぞっている場合
            #     ラインを外したら右へ曲がりラインを探す
            # 例: センサーがラインの右側をなぞっている場合
            #     ラインを外したら左へ曲がりラインを探す
            # 
            # ここでは、単純にラインを外したら右に曲がってラインを探す例
            robot.turn_right(BASE_SPEED, TURN_ADJUST) # ラインに戻るために曲がる
            print("右旋回 (ライン探索)")

 utime.sleep_ms(10)

except KeyboardInterrupt:
    print("¥nプログラム終了")
    robot.stop()
    # 必要に応じてPWMを停止（MicroPythonのPWMはstopメソッドがない場合が多い）
    # pwm_left.deinit()
    # pwm_right.deinit()

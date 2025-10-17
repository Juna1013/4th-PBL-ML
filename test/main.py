from machine import Pin, PWM
import time

try:
    import rp2
except ImportError:
    rp2 = None

# ==== ピン設定 ====
MOTOR_LEFT_FWD = 5
MOTOR_LEFT_REV = 4
MOTOR_RIGHT_FWD = 3
MOTOR_RIGHT_REV = 2

MOTOR_PINS = [MOTOR_LEFT_FWD, MOTOR_LEFT_REV, MOTOR_RIGHT_FWD, MOTOR_RIGHT_REV]

PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]
SENSOR_WEIGHTS = [-7, -5, -3, -1, 1, 3, 5, 7]

BASE_SPEED = 15000
MAX_SPEED = 54613
MIN_SPEED = 5000  # 左右モーターの最低速度
KP = 50
KD = 10

# ==== モーター制御 ====
class MotorController:
    def __init__(self):
        # 左右モーター前進・後退用PWMを作成
        self.motors = [PWM(Pin(p)) for p in MOTOR_PINS]
        for m in self.motors:
            m.freq(1000)

    def set_speed(self, left, right):
        # 左モーター：前進ピンに0、後退ピンに速度（元のまま）
        self.motors[0].duty_u16(0)           # 左前進ピン
        self.motors[1].duty_u16(int(left))   # 左後退ピン

        # 右モーター：前進ピンに速度、後退ピンに0（右だけ逆回転）
        self.motors[2].duty_u16(int(right))  # 右前進ピン
        self.motors[3].duty_u16(0)           # 右後退ピン

    def stop(self):
        for m in self.motors:
            m.duty_u16(0)

# ==== ラインセンサー ====
class LineSensor:
    def __init__(self):
        self.sensors = [Pin(p, Pin.IN) for p in PHOTOREFLECTOR_PINS]
        self.last_position = 0

    def get_line_position(self):
        values = [s.value() for s in self.sensors]
        weighted_sum = sum(SENSOR_WEIGHTS[i] for i, v in enumerate(values) if v == 0)
        count = sum(1 for v in values if v == 0)
        if count > 0:
            position = weighted_sum / count
            self.last_position = position
            return position, True
        return self.last_position, False

# ==== ライントレーサ ====
class LineTracer:
    def __init__(self):
        self.motor = MotorController()
        self.sensor = LineSensor()
        self.last_error = 0
        self.running = False
        self.led = Pin("LED", Pin.OUT)

    def pd_control(self, position, on_line):
        if not on_line:
            # 線を見失った場合は前回の方向で旋回
            return (MIN_SPEED, BASE_SPEED) if self.last_error < 0 else (BASE_SPEED, MIN_SPEED)

        error = position
        correction = int(KP * error + KD * (error - self.last_error))
        self.last_error = error

        # 左右速度を MIN_SPEED〜MAX_SPEED の範囲で制限
        left = max(MIN_SPEED, min(MAX_SPEED, BASE_SPEED - correction))
        right = max(MIN_SPEED, min(MAX_SPEED, BASE_SPEED + correction))
        return left, right

    def wait_for_bootsel_release(self):
        if rp2:
            while rp2.bootsel_button():
                time.sleep(0.05)

    def run(self):
        prev_button = False
        try:
            while True:
                button_pressed = rp2 and rp2.bootsel_button()

                # BootselボタンでON/OFF切替
                if button_pressed and not prev_button:
                    self.wait_for_bootsel_release()
                    self.running = not self.running
                    self.led.value(1 if self.running else 0)
                    if not self.running:
                        self.motor.stop()
                    time.sleep(0.2)

                prev_button = button_pressed

                if self.running:
                    position, on_line = self.sensor.get_line_position()
                    left, right = self.pd_control(position, on_line)
                    self.motor.set_speed(left, right)
                else:
                    self.motor.stop()

                time.sleep(0.01)

        except KeyboardInterrupt:
            pass
        finally:
            self.motor.stop()
            self.led.off()

# ==== メイン実行 ====
if __name__ == "__main__":
    LineTracer().run()


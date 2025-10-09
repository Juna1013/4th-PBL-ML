from machine import Pin, PWM
import time

try:
    import rp2
except ImportError:
    rp2 = None

# 設定
# モーターピン設定（MakerDrive）
MOTOR_LEFT_FWD = 5   # M1A
MOTOR_LEFT_REV = 4   # M1B  
MOTOR_RIGHT_FWD = 3  # M2A
MOTOR_RIGHT_REV = 2  # M2B
MOTOR_PINS = [MOTOR_LEFT_FWD, MOTOR_LEFT_REV, MOTOR_RIGHT_FWD, MOTOR_RIGHT_REV]

# フォトリフレクタピン（左から右へ8個）
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]
SENSOR_PINS = PHOTOREFLECTOR_PINS

# センサー重み（左から右へ）
SENSOR_WEIGHTS = [-7, -5, -3, -1, 1, 3, 5, 7]

# 速度設定
BASE_SPEED = 30000  # 基本速度（0-65535）
MAX_SPEED = 54613   # 最大速度
LINE_TRACE_SPEED_PERCENT = 83  # ライントレース時の速度

# PID制御パラメータ
KP = 50  # 比例ゲイン
KI = 0   # 積分ゲイン（未使用）
KD = 10  # 微分ゲイン

# デバッグ設定
DEBUG_INTERVAL = 20  # デバッグ表示の間隔（ループ回数）

class MotorController:
    def __init__(self):
        self.motors = [PWM(Pin(p)) for p in MOTOR_PINS]
        for m in self.motors:
            m.freq(1000)

    def set_speed(self, left, right):
        self.motors[0].duty_u16(int(left))
        self.motors[1].duty_u16(0)
        self.motors[2].duty_u16(int(right))
        self.motors[3].duty_u16(0)

    def stop(self):
        for m in self.motors:
            m.duty_u16(0)

class LineSensor:
    def __init__(self):
        self.sensors = [Pin(p, Pin.IN) for p in SENSOR_PINS]
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

    def debug_string(self):
        values = [s.value() for s in self.sensors]
        visual = ''.join('■' if v == 0 else '□' for v in values)
        pos, on_line = self.get_line_position()
        return f"{visual} | {pos:+.1f} | {'ON' if on_line else 'LOST'}"

class LineTracer:
    def __init__(self):
        self.motor = MotorController()
        self.sensor = LineSensor()
        self.last_error = 0

    def pd_control(self, position, on_line):
        if not on_line:
            return (0, BASE_SPEED) if self.last_error < 0 else (BASE_SPEED, 0)
        
        error = position
        correction = int(KP * error + KD * (error - self.last_error))
        self.last_error = error
        
        left = max(0, min(MAX_SPEED, BASE_SPEED - correction))
        right = max(0, min(MAX_SPEED, BASE_SPEED + correction))
        return left, right

    def run(self):
        print("ライントレース開始")
        
        if rp2:
            print("BOOTSELでスタート")
            while rp2.bootsel_button() == 0:
                time.sleep(0.1)
            time.sleep(0.5)
        else:
            time.sleep(3)

        loop_count = 0
        try:
            while True:
                if rp2 and rp2.bootsel_button() == 1:
                    break
                
                position, on_line = self.sensor.get_line_position()
                left, right = self.pd_control(position, on_line)
                self.motor.set_speed(left, right)
                
                loop_count += 1
                if loop_count % 20 == 0:
                    print(self.sensor.debug_string())
                
                time.sleep(0.01)
        except KeyboardInterrupt:
            pass
        finally:
            self.motor.stop()
            print("終了")

if __name__ == "__main__":
    LineTracer().run()

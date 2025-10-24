from machine import Pin, PWM
import time

# ピン設定
MOTOR_LEFT_FWD = 5
MOTOR_LEFT_REV = 4
MOTOR_RIGHT_FWD = 3
MOTOR_RIGHT_REV = 2

PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]

# テスト用パラメータ
TEST_SPEED = 6000   # 安全な低速
STOP_SPEED = 0

# モーター制御
class MotorController:
    def __init__(self):
        self.motors = [PWM(Pin(p)) for p in [MOTOR_LEFT_FWD, MOTOR_LEFT_REV, MOTOR_RIGHT_FWD, MOTOR_RIGHT_REV]]
        for m in self.motors:
            m.freq(1000)

    def forward(self, speed=TEST_SPEED):
        # 左モーター：後退ピン使用、右モーター：前進ピン使用
        self.motors[0].duty_u16(0)
        self.motors[1].duty_u16(speed)
        self.motors[2].duty_u16(speed)
        self.motors[3].duty_u16(0)

    def stop(self):
        for m in self.motors:
            m.duty_u16(0)

# ラインセンサ
class LineSensor:
    def __init__(self):
        self.sensors = [Pin(p, Pin.IN) for p in PHOTOREFLECTOR_PINS]

    def is_line_detected(self):
        # 0=黒線, 1=白地 のデジタル入力
        values = [s.value() for s in self.sensors]
        return 0 in values  # 黒線（0）が1つでもあれば検出
    
# テスト制御
class LineTracerTest:
    def __init__(self):
        self.motor = MotorController()
        self.sensor = LineSensor()
        self.led = Pin("LED", Pin.OUT)

        # 起動確認：LED点滅3回
        for _ in range(3):
            self.led.on()
            time.sleep(0.2)
            self.led.off()
            time.sleep(0.2)

    def run(self):
        try:
            while True:
                # 黒線検出で停止＋LED点灯、白地で前進＋LED消灯
                if self.sensor.is_line_detected():
                    self.motor.stop()
                    self.led.on()
                else:
                    self.motor.forward(TEST_SPEED)
                    self.led.off()

                time.sleep(0.05)

        except KeyboardInterrupt:
            pass
        finally:
            self.motor.stop()
            self.led.off()

# メイン実行
if __name__ == "__main__":
    LineTracerTest().run()

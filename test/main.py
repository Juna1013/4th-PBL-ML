from machine import Pin, PWM
import time

try:
    import rp2
except ImportError:
    rp2 = None

# ==== 設定 ====
MOTOR_LEFT_FWD = 5
MOTOR_LEFT_REV = 4
MOTOR_RIGHT_FWD = 3
MOTOR_RIGHT_REV = 2
MOTOR_PINS = [MOTOR_LEFT_FWD, MOTOR_LEFT_REV, MOTOR_RIGHT_FWD, MOTOR_RIGHT_REV]

PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]
SENSOR_WEIGHTS = [-7, -5, -3, -1, 1, 3, 5, 7]

BASE_SPEED = 30000
MAX_SPEED = 54613
KP = 50
KD = 10

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

class LineTracer:
    def __init__(self):
        self.motor = MotorController()
        self.sensor = LineSensor()
        self.last_error = 0
        self.running = False  # ON/OFF状態
        self.led = Pin("LED", Pin.OUT)  # 状態確認用（ON=点灯）

    def pd_control(self, position, on_line):
        if not on_line:
            return (0, BASE_SPEED) if self.last_error < 0 else (BASE_SPEED, 0)
        error = position
        correction = int(KP * error + KD * (error - self.last_error))
        self.last_error = error
        left = max(0, min(MAX_SPEED, BASE_SPEED - correction))
        right = max(0, min(MAX_SPEED, BASE_SPEED + correction))
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

                # ボタン押下でON/OFF切り替え
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

if __name__ == "__main__":
    LineTracer().run()

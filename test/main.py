from machine import Pin, PWM
import time
import config

try:
    import rp2
except ImportError:
    rp2 = None

# ===== 設定 (config.pyからインポート) =====
# モーターピン（MakerDrive: GPIO 2-5）
M1A_PIN = config.MOTOR_LEFT_FWD
M1B_PIN = config.MOTOR_LEFT_REV
M2A_PIN = config.MOTOR_RIGHT_FWD
M2B_PIN = config.MOTOR_RIGHT_REV

# フォトリフレクタピン（左から右へ8個）
SENSOR_PINS = config.PHOTOREFLECTOR_PINS

# センサー重み（左から右へ）
SENSOR_WEIGHTS = config.SENSOR_WEIGHTS

# 制御パラメータ
BASE_SPEED = config.BASE_SPEED
MAX_SPEED = config.MAX_SPEED
KP = config.KP
KD = config.KD


class MotorController:
    """モーター制御クラス"""

    def __init__(self):
        self.m1a = PWM(Pin(M1A_PIN))
        self.m1b = PWM(Pin(M1B_PIN))
        self.m2a = PWM(Pin(M2A_PIN))
        self.m2b = PWM(Pin(M2B_PIN))

        # PWM周波数設定
        for motor in [self.m1a, self.m1b, self.m2a, self.m2b]:
            motor.freq(1000)

    def set_speed(self, left, right):
        """左右モーターの速度を設定"""
        self.m1a.duty_u16(int(left))
        self.m1b.duty_u16(0)
        self.m2a.duty_u16(int(right))
        self.m2b.duty_u16(0)

    def stop(self):
        """モーター停止"""
        self.m1a.duty_u16(0)
        self.m1b.duty_u16(0)
        self.m2a.duty_u16(0)
        self.m2b.duty_u16(0)


class LineSensor:
    """ライン�ンサークラス"""

    def __init__(self, pins, weights):
        self.sensors = [Pin(pin, Pin.IN) for pin in pins]
        self.weights = weights
        self.last_position = 0

    def read_all(self):
        """全センサーの値を読む（0=黒/ライン, 1=白/背景）"""
        return [s.value() for s in self.sensors]

    def get_line_position(self):
        """
        重み付け平均でライン位置を計算

        戻り値:
            position: -7 ~ +7 (負=左, 正=右)
            on_line: ラインを検出しているか
        """
        values = self.read_all()
        weighted_sum = 0
        count = 0

        for i, value in enumerate(values):
            if value == 0:  # 黒検出
                weighted_sum += self.weights[i]
                count += 1

        if count > 0:
            position = weighted_sum / count
            self.last_position = position
            return position, True
        else:
            return self.last_position, False

    def get_debug_string(self):
        """デバッグ用文字列"""
        values = self.read_all()
        visual = ''.join(['■' if v == 0 else '□' for v in values])
        position, on_line = self.get_line_position()
        status = "ON" if on_line else "LOST"
        return f"{visual} | Pos:{position:+.1f} | {status}"


class LineTracer:
    """ライントレース制御クラス"""

    def __init__(self):
        self.motor = MotorController()
        self.sensor = LineSensor(SENSOR_PINS, SENSOR_WEIGHTS)
        self.last_error = 0

    def pd_control(self, line_position, on_line):
        """PD制御でモーター速度を計算"""
        if not on_line:
            # ラインロスト時は前回の誤差で探索
            if self.last_error < 0:
                return 0, BASE_SPEED  # 左探索
            else:
                return BASE_SPEED, 0  # 右探索

        # PD制御
        error = line_position
        derivative = error - self.last_error
        correction = int(KP * error + KD * derivative)
        self.last_error = error

        # モーター速度計算
        left_speed = BASE_SPEED - correction
        right_speed = BASE_SPEED + correction

        # 速度制限
        left_speed = max(0, min(MAX_SPEED, left_speed))
        right_speed = max(0, min(MAX_SPEED, right_speed))

        return left_speed, right_speed

    def run(self):
        """ライントレース実行"""
        print("=" * 50)
        print("テスト用ライントレース")
        print("=" * 50)
        print(f"センサー: {len(SENSOR_PINS)}個")
        print(f"重み: {SENSOR_WEIGHTS}")
        print(f"PID: Kp={KP}, Kd={KD}")
        print()

        # スタート待機
        if rp2:
            print("BOOTSELボタンを押してスタート...")
            while rp2.bootsel_button() == 0:
                time.sleep(0.1)
            time.sleep(0.5)
        else:
            print("3秒後にスタート...")
            time.sleep(3)

        print("スタート!\n")

        loop_count = 0
        start_time = time.time()

        try:
            while True:
                # 停止チェック
                if rp2 and rp2.bootsel_button() == 1:
                    print("\nBOOTSELで停止")
                    break

                # ライン位置取得
                position, on_line = self.sensor.get_line_position()

                # PD制御
                left, right = self.pd_control(position, on_line)

                # モーター駆動
                self.motor.set_speed(left, right)

                # デバッグ表示（20ループごと）
                loop_count += 1
                if loop_count % 20 == 0:
                    print(self.sensor.get_debug_string())

                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\nCtrl+Cで停止")
        finally:
            self.motor.stop()
            elapsed = time.time() - start_time
            print(f"\n走行時間: {elapsed:.1f}秒")
            print("終了")


# メイン実行
if __name__ == "__main__":
    tracer = LineTracer()
    tracer.run()

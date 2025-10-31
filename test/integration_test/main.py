# line_trace_main.py
from machine import Pin, PWM
import time
import math

# --- ピン定義（motor_test.py に準拠） ---
LEFT_FWD_PIN = 5
LEFT_REV_PIN = 4
RIGHT_FWD_PIN = 2
RIGHT_REV_PIN = 3
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]
LED_PIN = "LED"

# --- 走行パラメータ ---
WHEEL_DIAMETER = 3.0    # cm
MOTOR_MAX_RPM = 10000
TARGET_SPEED = 5.0      # cm/s（参考）
MIN_PWM = 25000         # モーターが確実に回る最低PWM

# --- PWM出力基準値を計算 ---
circumference = math.pi * WHEEL_DIAMETER
target_rpm = (TARGET_SPEED / circumference) * 60
base_speed_calc = int(target_rpm / MOTOR_MAX_RPM * 65535)
BASE_SPEED = max(base_speed_calc // 4, MIN_PWM)
print(f"計算された BASE_SPEED: {BASE_SPEED}")

# --- モーター初期化 ---
left_fwd = PWM(Pin(LEFT_FWD_PIN))
left_rev = PWM(Pin(LEFT_REV_PIN))
right_fwd = PWM(Pin(RIGHT_FWD_PIN))
right_rev = PWM(Pin(RIGHT_REV_PIN))
for pwm in [left_fwd, left_rev, right_fwd, right_rev]:
    pwm.freq(1000)

# --- センサー初期化 ---
sensors = [Pin(p, Pin.IN) for p in PHOTOREFLECTOR_PINS]

# --- LED初期化 ---
led = Pin(LED_PIN, Pin.OUT)
led.value(1)

# --- モーター制御関数 ---
def set_motors(left_duty, right_duty):
    left_duty = max(MIN_PWM, min(65535, int(left_duty)))
    right_duty = max(MIN_PWM, min(65535, int(right_duty)))

    # 左モーター前進
    left_fwd.duty_u16(left_duty)
    left_rev.duty_u16(0)

    # 右モーターは逆接続（REV側にPWM）
    right_fwd.duty_u16(0)
    right_rev.duty_u16(right_duty)

def stop_motors():
    for pwm in [left_fwd, left_rev, right_fwd, right_rev]:
        pwm.duty_u16(0)
    print("=== モーター停止 ===")

# --- ライントレース制御パラメータ ---
KP = 8000
WEIGHTS = [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5]  # センサー配置に対応

print("=== ライントレース開始 ===")
last_error = 0

try:
    while True:
        # 各フォトリフレクタの状態を取得
        values = [s.value() for s in sensors]

        # 必要なら反転（黒=0, 白=1 の場合は次の行を有効化）
        # values = [1 - v for v in values]

        line_detected = sum(values)
        if line_detected == 0:
            # 線が見えないときは前回の誤差を保持（直進維持）
            error = last_error
        else:
            # センサー重み付き平均で偏差を計算
            error = sum(WEIGHTS[i] * values[i] for i in range(8)) / line_detected
            last_error = error

        # 偏差に比例した旋回量を計算
        turn = KP * error
        left_speed = BASE_SPEED - turn
        right_speed = BASE_SPEED + turn

        set_motors(left_speed, right_speed)
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("\n=== 割り込み検出 ===")

finally:
    stop_motors()
    led.value(0)
    print("=== プログラム終了 ===")

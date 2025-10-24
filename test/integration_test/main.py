from machine import Pin, PWM
import time
import math

# --- ピン定義 ---
LEFT_FWD_PIN = 5
LEFT_REV_PIN = 4
RIGHT_FWD_PIN = 3
RIGHT_REV_PIN = 2
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]
LED_PIN = "LED"

# --- 車体・速度設定 ---
WHEEL_DIAMETER = 3.0    # cm
MOTOR_MAX_RPM = 10000    # モーター最大RPM
TARGET_SPEED = 5.0       # cm/s
MIN_PWM = 20000          # モーターが確実に回る最低PWM値

# 1回転で進む距離
circumference = math.pi * WHEEL_DIAMETER
# 目標回転数(RPM)
target_rpm = (TARGET_SPEED / circumference) * 60
# PWMデューティ比
base_speed_calc = int(target_rpm / MOTOR_MAX_RPM * 65535)
# 最低PWMを確保
BASE_SPEED = max(base_speed_calc, MIN_PWM)

print(f"計算されたBASE_SPEED: {BASE_SPEED}")

# --- モーター初期化 ---
left_fwd = PWM(Pin(LEFT_FWD_PIN))
left_rev = PWM(Pin(LEFT_REV_PIN))
right_fwd = PWM(Pin(RIGHT_FWD_PIN))
right_rev = PWM(Pin(RIGHT_REV_PIN))
left_fwd.freq(1000)
left_rev.freq(1000)
right_fwd.freq(1000)
right_rev.freq(1000)

# --- センサー初期化 ---
sensors = [Pin(p, Pin.IN) for p in PHOTOREFLECTOR_PINS]

# --- LED初期化 ---
led = Pin(LED_PIN, Pin.OUT)
led.value(1)  # 常時点灯

# --- モーター制御関数 ---
def set_motors(left_duty, right_duty):
    # デューティ比のクリッピング
    left_duty = max(MIN_PWM, min(65535, int(left_duty)))
    right_duty = max(MIN_PWM, min(65535, int(right_duty)))

    # 左モーター: 通常前進
    left_fwd.duty_u16(left_duty)
    left_rev.duty_u16(0)

    # 右モーター: 逆転
    right_fwd.duty_u16(0)
    right_rev.duty_u16(right_duty)

def stop_motors():
    left_fwd.duty_u16(0)
    left_rev.duty_u16(0)
    right_fwd.duty_u16(0)
    right_rev.duty_u16(0)
    print("=== モーター停止 ===")

# --- ライントレース制御パラメータ ---
KP = 8000
WEIGHTS = [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5]

print("=== ライントレース常時走行開始 ===")
last_error = 0  # ラインロスト時に前回のエラーを保持

try:
    while True:
        # 1. センサー値取得
        values = [s.value() for s in sensors]
        # 黒=0, 白=1 の場合は以下を有効化
        # values = [1 - v for v in values]

        line_detected_count = sum(values)

        if line_detected_count == 0:
            # ラインロスト時は前回の誤差で走行
            error = last_error
        else:
            # ラインの偏差計算
            error = sum(WEIGHTS[i] * values[i] for i in range(8)) / line_detected_count
            last_error = error

        # 2. P制御で左右モーター速度計算
        turn = KP * error
        left_speed = BASE_SPEED - turn
        right_speed = BASE_SPEED + turn

        # 3. モーター出力
        set_motors(left_speed, right_speed)

        # ループ周期
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("\n割り込み検出。")

finally:
    stop_motors()
    led.value(0)
    print("=== プログラム終了 ===")

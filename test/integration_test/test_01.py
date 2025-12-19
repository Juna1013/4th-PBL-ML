# line_trace_main.py
from machine import Pin, PWM
import time

# ピン定義

# モーターピン（正しい配線） 
LEFT_FWD_PIN = 5
LEFT_REV_PIN = 4
RIGHT_FWD_PIN = 2
RIGHT_REV_PIN = 3

# センサーピン（8chデジタルセンサー） 
# センサー1-8の配置（左から右へ）
# 1:GP22, 2:GP21, 3:GP28, 4:GP27, 5:GP26, 6:GP18, 7:GP17, 8:GP16
SENSOR_PINS = [22, 21, 28, 27, 26, 18, 17, 16]

LED_PIN = "LED"

# 走行パラメータ
MIN_PWM = 5000  # モーターが確実に回る最低PWM
BASE_SPEED = 10000  # ベース速度

# モーター補正係数（右モーターがREVピン駆動で速いため出力を抑える）
LEFT_MOTOR_CORRECTION = 1.0   # 左モーターは100%
RIGHT_MOTOR_CORRECTION = 1.0 # 右モーターは100%

# モーター初期化
left_fwd = PWM(Pin(LEFT_FWD_PIN))
left_rev = PWM(Pin(LEFT_REV_PIN))
right_fwd = PWM(Pin(RIGHT_FWD_PIN))
right_rev = PWM(Pin(RIGHT_REV_PIN))
for pwm in [left_fwd, left_rev, right_fwd, right_rev]:
    pwm.freq(1000)

# センサー初期化（デジタル入力、プルアップ） 
sensors = [Pin(p, Pin.IN, Pin.PULL_UP) for p in SENSOR_PINS]

# LED初期化
led = Pin(LED_PIN, Pin.OUT)
led.value(1)

# モーター制御関数
def set_motors(left_duty, right_duty):
    # 補正係数を適用
    left_duty = int(left_duty * LEFT_MOTOR_CORRECTION)
    right_duty = int(right_duty * RIGHT_MOTOR_CORRECTION)
    
    # PWM範囲に制限
    left_duty = max(MIN_PWM, min(65535, left_duty))
    right_duty = max(MIN_PWM, min(65535, right_duty))

    # 左モーター前進（FWDピンで駆動）
    left_fwd.duty_u16(left_duty)
    left_rev.duty_u16(0)

    # 右モーターは逆接続（REVピンで駆動 - REVの方が速いため補正係数で調整）
    right_fwd.duty_u16(0)
    right_rev.duty_u16(right_duty)

def stop_motors():
    for pwm in [left_fwd, left_rev, right_fwd, right_rev]:
        pwm.duty_u16(0)
    print("=== モーター停止 ===")

# ライントレース制御パラメータ
KP = 1000  # 8センサー用に調整
# 8つのセンサーの重み: 左端(-3.5)から右端(+3.5)まで
WEIGHTS = [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5]

print("=== ライントレース開始（8chデジタルセンサー） ===")
last_error = 0
last_debug_time = 0

try:
    while True:
        # デジタルピンから直接センサー値を読み取り（0=黒検出, 1=白検出）
        values = [s.value() for s in sensors]

        # デバッグ表示（0.5秒に1回）
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_debug_time) > 500:
            last_debug_time = current_time
            led.toggle()
            print("センサー状態:", " ".join(str(v) for v in values))

        # 黒ライン（0）を検知したセンサーで重み付き平均を計算
        detected_count = 0
        weighted_sum = 0.0
        for i in range(8):
            if values[i] == 0:  # 黒を検知
                weighted_sum += WEIGHTS[i]
                detected_count += 1

        if detected_count == 0:
            # 線が見えないときは前回の誤差を保持（直進維持）
            error = last_error
        else:
            # センサー重み付き平均で偏差を計算（符号を反転）
            error = -(weighted_sum / detected_count)
            last_error = error

        # 偏差に比例した旋回量を計算
        turn = int(KP * error)
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

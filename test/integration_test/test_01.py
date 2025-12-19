'''
- KP（比例ゲイン）が小さい
誤差に対して旋回量が足りず、カーブで外に膨らむ。
- KD（微分ゲイン）が弱い／未調整
急カーブで誤差変化に追従できず、遅れてしまう。
- ベース速度が速すぎる
直線は快適でも、カーブでオーバーシュートして曲がり切れない。
- 減速制御が弱い
誤差が大きいときに速度を落とさないと、物理的に曲がれない。
'''

from machine import Pin, PWM
import time

# ピン定義
LEFT_FWD_PIN = 5
LEFT_REV_PIN = 4
RIGHT_FWD_PIN = 2
RIGHT_REV_PIN = 3

SENSOR_PINS = [22, 21, 28, 27, 26, 18, 17, 16]
LED_PIN = "LED"

# 走行パラメータ
BASE_SPEED = 8000   # 少し落とす
LEFT_MOTOR_CORRECTION = 0.77
RIGHT_MOTOR_CORRECTION = 1.0

# モーター初期化
left_fwd = PWM(Pin(LEFT_FWD_PIN))
left_rev = PWM(Pin(LEFT_REV_PIN))
right_fwd = PWM(Pin(RIGHT_FWD_PIN))
right_rev = PWM(Pin(RIGHT_REV_PIN))
for pwm in [left_fwd, left_rev, right_fwd, right_rev]:
    pwm.freq(1000)

# センサー初期化
sensors = [Pin(p, Pin.IN, Pin.PULL_UP) for p in SENSOR_PINS]

# LED初期化
led = Pin(LED_PIN, Pin.OUT)
led.value(1)

# モーター制御関数
def set_motors(left_duty, right_duty):
    left_duty = int(left_duty * LEFT_MOTOR_CORRECTION)
    right_duty = int(right_duty * RIGHT_MOTOR_CORRECTION)

    # PWM範囲に制限（ゼロ許容）
    left_duty = max(0, min(65535, left_duty))
    right_duty = max(0, min(65535, right_duty))

    left_fwd.duty_u16(left_duty)
    left_rev.duty_u16(0)

    right_fwd.duty_u16(0)
    right_rev.duty_u16(right_duty)

def stop_motors():
    for pwm in [left_fwd, left_rev, right_fwd, right_rev]:
        pwm.duty_u16(0)
    print("=== モーター停止 ===")

# ライントレース制御パラメータ
KP = 7000   # 比例ゲイン強め
KD = 3000   # 微分ゲイン追加
WEIGHTS = [-7, -5, -3, -1, 1, 3, 5, 7]

print("=== ライントレース開始（改良版） ===")
last_error = 0
last_debug_time = 0

try:
    while True:
        values = [s.value() for s in sensors]

        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_debug_time) > 500:
            last_debug_time = current_time
            led.toggle()
            print("センサー状態:", " ".join(str(v) for v in values))

        detected_count = 0
        weighted_sum = 0.0
        for i in range(8):
            if values[i] == 0:
                weighted_sum += WEIGHTS[i]
                detected_count += 1

        if detected_count == 0:
            error = last_error
        else:
            error = -(weighted_sum / detected_count)

        # PD制御
        error_diff = error - last_error
        turn = int(KP * error + KD * error_diff)
        last_error = error

        # ターン量を制限
        turn = max(-BASE_SPEED, min(BASE_SPEED, turn))

        # 誤差に応じて減速
        speed_factor = max(0.4, 1.0 - abs(error)/6)
        left_speed = int((BASE_SPEED - turn) * speed_factor)
        right_speed = int((BASE_SPEED + turn) * speed_factor)

        set_motors(left_speed, right_speed)
        time.sleep_ms(10)  # 制御周期をさらに短縮

except KeyboardInterrupt:
    print("\n=== 割り込み検出 ===")

finally:
    stop_motors()
    led.value(0)
    print("=== プログラム終了 ===")

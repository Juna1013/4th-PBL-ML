from machine import Pin, PWM
import time

# --- ピン定義 ---
LEFT_FWD_PIN = 5
LEFT_REV_PIN = 4
RIGHT_FWD_PIN = 3
RIGHT_REV_PIN = 2
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]
LED_PIN = "LED"

# --- 初期化 ---
left_fwd = PWM(Pin(LEFT_FWD_PIN))
left_rev = PWM(Pin(LEFT_REV_PIN))
right_fwd = PWM(Pin(RIGHT_FWD_PIN))
right_rev = PWM(Pin(RIGHT_REV_PIN))
left_fwd.freq(1000)
left_rev.freq(1000)
right_fwd.freq(1000)
right_rev.freq(1000)

sensors = [Pin(p, Pin.IN) for p in PHOTOREFLECTOR_PINS]
led = Pin(LED_PIN, Pin.OUT)
led.value(1)  # 動作中LED点灯

# --- モーター制御関数 ---
def set_motors(left_duty, right_duty):
    # 方向を逆転させる場合、FWDとREVを入れ替える
    left_duty = max(0, min(65535, int(left_duty)))
    right_duty = max(0, min(65535, int(right_duty)))

    # 左右モーターの方向逆転
    left_fwd.duty_u16(0)
    left_rev.duty_u16(left_duty)   # 前進用にREVピンを使用
    right_fwd.duty_u16(0)
    right_rev.duty_u16(right_duty) # 前進用にREVピンを使用

def stop_motors():
    left_fwd.duty_u16(0)
    left_rev.duty_u16(0)
    right_fwd.duty_u16(0)
    right_rev.duty_u16(0)
    print("=== モーター停止 ===")

# --- ライントレースパラメータ ---
BASE_SPEED = 30000 // 5  # 元の速度の1/5
KP = 8000
WEIGHTS = [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5]

# --- メインループ ---
print("=== ライントレース常時走行開始 ===")
last_error = 0

try:
    while True:
        values = [s.value() for s in sensors]
        # values = [1 - v for v in values]  # 黒=0, 白=1の場合はこちらを有効化

        line_detected_count = sum(values)

        if line_detected_count == 0:
            error = last_error
        else:
            error = sum(WEIGHTS[i] * values[i] for i in range(8)) / line_detected_count
            last_error = error

        turn = KP * error
        left_speed = BASE_SPEED - turn
        right_speed = BASE_SPEED + turn
        set_motors(left_speed, right_speed)

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("\n割り込み検出。")

finally:
    stop_motors()
    led.value(0)
    print("=== プログラム終了 ===")

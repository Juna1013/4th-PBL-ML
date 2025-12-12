# line_trace_main.py
from machine import Pin, PWM, ADC
import time

# =====================================================
# ピン定義
# =====================================================

# --- モーターピン（正しい配線） ---
LEFT_FWD_PIN = 5
LEFT_REV_PIN = 4
RIGHT_FWD_PIN = 2
RIGHT_REV_PIN = 3

# --- センサーピン（sensor_test.pyと同じ3chアナログセンサー） ---
# GP26=右, GP27=中, GP28=左
adc_right = ADC(Pin(26))
adc_center = ADC(Pin(27))
adc_left = ADC(Pin(28))

# センサー閾値（これより大きいと「1:白」、小さいと「0:黒」）
THRESHOLD = 30000

LED_PIN = "LED"

# --- 走行パラメータ ---
MIN_PWM = 3000  # モーターが確実に回る最低PWM
BASE_SPEED = 5000  # ベース速度

# モーター補正係数（右モーターがREVピン駆動で速いため出力を抑える）
LEFT_MOTOR_CORRECTION = 1.0   # 左モーターは100%
RIGHT_MOTOR_CORRECTION = 0.9 # 右モーターの出力を85%に抑える

# --- モーター初期化 ---
left_fwd = PWM(Pin(LEFT_FWD_PIN))
left_rev = PWM(Pin(LEFT_REV_PIN))
right_fwd = PWM(Pin(RIGHT_FWD_PIN))
right_rev = PWM(Pin(RIGHT_REV_PIN))
for pwm in [left_fwd, left_rev, right_fwd, right_rev]:
    pwm.freq(1000)

# --- LED初期化 ---
led = Pin(LED_PIN, Pin.OUT)
led.value(1)

# --- モーター制御関数 ---
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

# --- ライントレース制御パラメータ ---
KP = 3000  # 3センサー用に調整
# 3つのセンサーの重み: 左=-1, 中=0, 右=+1
WEIGHTS = [-1.0, 0.0, 1.0]

print("=== ライントレース開始（3chアナログセンサー） ===")
last_error = 0
last_debug_time = 0

try:
    while True:
        # センサー値の読み取り
        val_l = adc_left.read_u16()
        val_c = adc_center.read_u16()
        val_r = adc_right.read_u16()
        
        # 0か1に変換（閾値より大きければ1:白、小さければ0:黒）
        res_l = 1 if val_l > THRESHOLD else 0
        res_c = 1 if val_c > THRESHOLD else 0
        res_r = 1 if val_r > THRESHOLD else 0
        
        # 値を配列にまとめる（左、中、右の順）
        values = [res_l, res_c, res_r]

        # デバッグ表示（0.5秒に1回）
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_debug_time) > 500:
            last_debug_time = current_time
            led.toggle()
            print(f"センサー状態: {res_l} {res_c} {res_r}")

        # 黒ライン（0）を検知したセンサーで重み付き平均を計算
        detected_count = 0
        weighted_sum = 0.0
        for i in range(3):
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

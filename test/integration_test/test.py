from machine import Pin, PWM
import time

# --- ピン定義 ---
LEFT_FWD_PIN = 5
LEFT_REV_PIN = 4
RIGHT_FWD_PIN = 2
RIGHT_REV_PIN = 3
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]
LED_PIN = "LED"

# --- 走行パラメータ ---
BASE_PWM = 12500        # 基本の速度 (0〜65535)
MIN_PWM = 10000         # モーターが回る最低限の値

# モーター速度補正係数（個体差を補正）
LEFT_MOTOR_CORRECTION = 1.0   # 左モーターの補正係数
RIGHT_MOTOR_CORRECTION = 0.8  # 右モーターの補正係数（右が速いので減速）

print("BASE_PWM:", BASE_PWM)

# --- モーターの準備 ---
left_fwd = PWM(Pin(LEFT_FWD_PIN))
left_rev = PWM(Pin(LEFT_REV_PIN))
right_fwd = PWM(Pin(RIGHT_FWD_PIN))
right_rev = PWM(Pin(RIGHT_REV_PIN))

# 周波数を1000Hzに設定
left_fwd.freq(1000)
left_rev.freq(1000)
right_fwd.freq(1000)
right_rev.freq(1000)

# --- センサーの準備 ---
sensors = []
for pin_num in PHOTOREFLECTOR_PINS:
    sensors.append(Pin(pin_num, Pin.IN))

# --- LEDの準備 ---
led = Pin(LED_PIN, Pin.OUT)
led.value(1)

# --- 制御用定数 ---
KP = 8000
WEIGHTS = [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5]

print("=== ライントレース開始 ===")
last_error = 0
last_debug_time = 0

try:
    while True:
        # 1. センサーの値を読む
        sensor_values = []
        for sensor in sensors:
            sensor_values.append(sensor.value())
        
        # 2. ラインの位置（誤差）を計算する
        weighted_sum = 0.0
        detected_count = 0
        
        # 8個のセンサーを順番に確認
        for i in range(8):
            if sensor_values[i] == 0:  # 黒(0)を検知したら
                weighted_sum = weighted_sum + WEIGHTS[i]
                detected_count = detected_count + 1
        
        # 誤差の決定
        error = 0
        if detected_count == 0:
            # ラインが見つからない時は前回の誤差を使う
            error = last_error
        else:
            # 平均をとって誤差とする（符号を反転）
            error = -(weighted_sum / detected_count)
            last_error = error
            
        # 4. モーターの速度を計算
        turn_amount = int(KP * error)

        # 補正係数を適用
        left_speed = (BASE_PWM - turn_amount) * LEFT_MOTOR_CORRECTION
        right_speed = (BASE_PWM + turn_amount) * RIGHT_MOTOR_CORRECTION

        # 速度が範囲を超えないように調整（クリップ処理）
        if left_speed < MIN_PWM: left_speed = MIN_PWM
        if left_speed > 65535: left_speed = 65535
        
        if right_speed < MIN_PWM: right_speed = MIN_PWM
        if right_speed > 65535: right_speed = 65535
        
        # 整数型に変換
        left_duty = int(left_speed)
        right_duty = int(right_speed)

        # 3. デバッグ表示（0.5秒に1回）
        # モーター出力値も表示するように変更
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_debug_time) > 500:
            last_debug_time = current_time
            # LEDを反転（チカチカさせる）
            if led.value() == 1:
                led.value(0)
            else:
                led.value(1)
            
            print("Sensors:", sensor_values, "Error:", error)
            print("Motor PWM - L:", left_duty, " R:", right_duty)

        # 5. モーターを動かす
        # 左モーター（正転ピンを使って前進）
        left_fwd.duty_u16(int(left_speed))
        left_rev.duty_u16(0)
        
        # 右モーター（正転ピンを使って前進）
        right_fwd.duty_u16(int(right_speed))
        right_rev.duty_u16(0)

        # 少し待つ
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("\n=== 停止 ===")

finally:
    # プログラム終了時は必ずモーターを止める
    left_fwd.duty_u16(0)
    left_rev.duty_u16(0)
    right_fwd.duty_u16(0)
    right_rev.duty_u16(0)
    led.value(0)
    print("=== 終了 ===")

from machine import Pin, PWM
import time
import network
import urequests
import ujson
import gc
import config

# ピン定義
LEFT_FWD_PIN = 5
LEFT_REV_PIN = 4
RIGHT_FWD_PIN = 2
RIGHT_REV_PIN = 3

SENSOR_PINS = [22, 21, 28, 27, 26, 18, 17, 16]
LED_PIN = "LED"

# 走行パラメータ
BASE_SPEED = 8000
LEFT_MOTOR_CORRECTION = 0.77
RIGHT_MOTOR_CORRECTION = 1.0

# ライントレース制御パラメータ
KP = 9000
KD = 3000
WEIGHTS = [-7, -5, -3, -1, 1, 3, 5, 7]

# WiFi/テレメトリ設定（最小限）
TELEMETRY_INTERVAL_MS = 3000  # 3秒ごと（負荷軽減）
TELEMETRY_URL = config.API_URL

# WiFi初期化（簡易版）
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print(f"WiFi接続中: {config.SSID}")
wlan.connect(config.SSID, config.PASSWORD)

# 最大3秒待機
timeout = 6
while not wlan.isconnected() and timeout > 0:
    print(".", end="")
    time.sleep(0.5)
    timeout -= 1

print()
if wlan.isconnected():
    print(f"WiFi接続成功! IP: {wlan.ifconfig()[0]}")
else:
    print("WiFi接続失敗 - ライントレースのみ実行")

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

# モーター制御関数（test_01.pyと完全に同じ）
def set_motors(left_duty, right_duty):
    left_duty = int(left_duty * LEFT_MOTOR_CORRECTION)
    right_duty = int(right_duty * RIGHT_MOTOR_CORRECTION)

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

# 簡易テレメトリ送信（最小限）
def send_data(sensors, left_speed, right_speed):
    try:
        gc.collect()
        data = {
            "timestamp": time.ticks_ms(),
            "sensors": sensors,
            "motor": {"left_speed": left_speed, "right_speed": right_speed}
        }
        response = urequests.post(TELEMETRY_URL, data=ujson.dumps(data), headers={'Content-Type': 'application/json'}, timeout=3)
        response.close()
        gc.collect()
        return True
    except:
        return False

print("=== ライントレース開始（改良版） ===")
last_error = 0
last_debug_time = 0
last_telemetry_time = 0
last_wifi_status = "-"  # WiFi送信状態（✓:成功, ✗:失敗, -:未送信）

try:
    while True:
        # test_01.pyと完全に同じライントレース処理
        values = [s.value() for s in sensors]

        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_debug_time) > 500:
            last_debug_time = current_time
            led.toggle()
            print(f"センサー状態: {' '.join(str(v) for v in values)} | WiFi: {last_wifi_status}")

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

        error_diff = error - last_error
        turn = int(KP * error + KD * error_diff)
        last_error = error

        turn = max(-BASE_SPEED, min(BASE_SPEED, turn))

        speed_factor = max(0.3, 1.0 - abs(error)/10)
        left_speed = int((BASE_SPEED - turn) * speed_factor)
        right_speed = int((BASE_SPEED + turn) * speed_factor)

        set_motors(left_speed, right_speed)
        
        # WiFi送信（最小限・非ブロッキング）
        if wlan.isconnected() and time.ticks_diff(current_time, last_telemetry_time) > TELEMETRY_INTERVAL_MS:
            last_telemetry_time = current_time
            if send_data(values, left_speed, right_speed):
                last_wifi_status = "✓"  # 送信成功
            else:
                last_wifi_status = "✗"  # 送信失敗

        time.sleep_ms(10)

except KeyboardInterrupt:
    print("\n=== 割り込み検出 ===")

finally:
    stop_motors()
    led.value(0)
    if wlan:
        wlan.disconnect()
        wlan.active(False)
    print("=== プログラム終了 ===")

# line_trace_with_api.py
# ライントレース + API送信統合版

from machine import Pin, PWM
import time
import network
import urequests
import json

# WiFi設定（config.pyから読み込む場合は import config を使用）
SSID = "Juna1013"
PASSWORD = "f94s7uu4"
SERVER_IP = "10.73.246.50"  # Next.jsサーバーのIPアドレス
SERVER_PORT = 3000

# ピン定義
LEFT_FWD_PIN = 5
LEFT_REV_PIN = 4
RIGHT_FWD_PIN = 2
RIGHT_REV_PIN = 3
SENSOR_PINS = [22, 21, 28, 27, 26, 18, 17, 16]
LED_PIN = "LED"

# 走行パラメータ
MIN_PWM = 5000
BASE_SPEED = 10000
LEFT_MOTOR_CORRECTION = 0.65
RIGHT_MOTOR_CORRECTION = 1.0
KP = 5000
WEIGHTS = [-7.0, -5.0, -3.0, -1.0, 1.0, 3.0, 5.0, 7.0]

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

# WiFi接続
print("=== WiFi接続開始 ===")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

while not wlan.isconnected():
    print("接続中...")
    time.sleep(1)

print("WiFi接続完了:", wlan.ifconfig()[0])

# サーバー接続テスト
try:
    ping_url = f"http://{SERVER_IP}:{SERVER_PORT}/api/ping"
    res = urequests.get(ping_url)
    print("サーバー応答:", res.text)
    res.close()
except Exception as e:
    print("サーバー接続エラー:", e)

# モーター制御関数
def set_motors(left_duty, right_duty):
    left_duty = int(left_duty * LEFT_MOTOR_CORRECTION)
    right_duty = int(right_duty * RIGHT_MOTOR_CORRECTION)
    
    left_duty = max(MIN_PWM, min(65535, left_duty))
    right_duty = max(MIN_PWM, min(65535, right_duty))

    left_fwd.duty_u16(left_duty)
    left_rev.duty_u16(0)
    right_fwd.duty_u16(0)
    right_rev.duty_u16(right_duty)
    
    return left_duty, right_duty

def stop_motors():
    for pwm in [left_fwd, left_rev, right_fwd, right_rev]:
        pwm.duty_u16(0)

# API送信関数
def send_sensor_data(sensor_values, left_speed, right_speed, error, status="running"):
    try:
        url = f"http://{SERVER_IP}:{SERVER_PORT}/api/sensor"
        
        payload = {
            "timestamp": time.ticks_ms(),
            "sensors": {
                "values": sensor_values,
                "lineDetected": any(v == 0 for v in sensor_values)
            },
            "motors": {
                "left": {
                    "speed": left_speed,
                    "direction": "forward"
                },
                "right": {
                    "speed": right_speed,
                    "direction": "forward"
                }
            },
            "error": error,
            "status": status
        }
        
        headers = {"Content-Type": "application/json"}
        response = urequests.post(url, data=json.dumps(payload), headers=headers)
        response.close()
        return True
    except Exception as e:
        print("API送信エラー:", e)
        return False

print("=== ライントレース + API送信開始 ===")
last_error = 0
last_debug_time = 0
last_api_send_time = 0
api_send_interval = 500  # 500msごとにAPI送信

try:
    while True:
        # センサー値読み取り
        values = [s.value() for s in sensors]
        current_time = time.ticks_ms()

        # デバッグ表示
        if time.ticks_diff(current_time, last_debug_time) > 500:
            last_debug_time = current_time
            led.toggle()
            print("センサー:", " ".join(str(v) for v in values))

        # エラー計算
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
            last_error = error

        # モーター制御
        turn = int(KP * error)
        left_speed = BASE_SPEED - turn
        right_speed = BASE_SPEED + turn
        actual_left, actual_right = set_motors(left_speed, right_speed)

        # API送信（一定間隔で）
        if time.ticks_diff(current_time, last_api_send_time) > api_send_interval:
            last_api_send_time = current_time
            send_sensor_data(values, actual_left, actual_right, error)

        time.sleep_ms(50)

except KeyboardInterrupt:
    print("\n=== 割り込み検出 ===")

finally:
    stop_motors()
    led.value(0)
    # 停止状態を送信
    send_sensor_data([1]*8, 0, 0, 0, "stopped")
    print("=== プログラム終了 ===")

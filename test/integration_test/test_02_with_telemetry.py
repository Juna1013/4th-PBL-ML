'''
ライントレース + テレメトリ送信プログラム
センサーとモーターの状態を外部サーバーにリアルタイムで送信
'''

from machine import Pin, PWM
import network
import time
import urequests
import ujson
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

# テレメトリ送信設定
TELEMETRY_INTERVAL_MS = 500  # 500msごとに送信
TELEMETRY_URL = f"http://{config.SERVER_IP}:8000/telemetry"

# WiFi接続
print("=== WiFi接続開始 ===")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config.SSID, config.PASSWORD)

while not wlan.isconnected():
    print("WiFi接続中...")
    time.sleep(1)

print("WiFi接続成功:", wlan.ifconfig()[0])

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

# グローバル変数（テレメトリ用）
current_left_speed = 0
current_right_speed = 0
current_sensor_values = [0] * 8
current_error = 0
current_turn = 0

# モーター制御関数
def set_motors(left_duty, right_duty):
    global current_left_speed, current_right_speed
    
    left_duty = int(left_duty * LEFT_MOTOR_CORRECTION)
    right_duty = int(right_duty * RIGHT_MOTOR_CORRECTION)

    # PWM範囲に制限
    left_duty = max(0, min(65535, left_duty))
    right_duty = max(0, min(65535, right_duty))
    
    # グローバル変数に保存
    current_left_speed = left_duty
    current_right_speed = right_duty

    left_fwd.duty_u16(left_duty)
    left_rev.duty_u16(0)

    right_fwd.duty_u16(0)
    right_rev.duty_u16(right_duty)

def stop_motors():
    global current_left_speed, current_right_speed
    for pwm in [left_fwd, left_rev, right_fwd, right_rev]:
        pwm.duty_u16(0)
    current_left_speed = 0
    current_right_speed = 0
    print("=== モーター停止 ===")

# テレメトリ送信関数
def send_telemetry():
    """センサーとモーターの状態をサーバーに送信"""
    try:
        data = {
            "timestamp": time.ticks_ms(),
            "sensors": current_sensor_values,
            "motor": {
                "left_speed": current_left_speed,
                "right_speed": current_right_speed
            },
            "control": {
                "error": current_error,
                "turn": current_turn,
                "base_speed": BASE_SPEED
            },
            "wifi": {
                "ip": wlan.ifconfig()[0],
                "rssi": wlan.status('rssi') if hasattr(wlan, 'status') else None
            }
        }
        
        json_data = ujson.dumps(data)
        headers = {'Content-Type': 'application/json'}
        
        response = urequests.post(TELEMETRY_URL, data=json_data, headers=headers)
        response.close()
        
    except Exception as e:
        print(f"テレメトリ送信エラー: {e}")

print("=== ライントレース開始（テレメトリ付き） ===")
last_error = 0
last_telemetry_time = 0

try:
    while True:
        # センサー読み取り
        values = [s.value() for s in sensors]
        current_sensor_values = values
        
        current_time = time.ticks_ms()
        
        # センサー検出処理
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
        
        current_error = error

        # PD制御
        error_diff = error - last_error
        turn = int(KP * error + KD * error_diff)
        current_turn = turn
        last_error = error

        # ターン量を制限
        turn = max(-BASE_SPEED, min(BASE_SPEED, turn))

        # 誤差に応じて減速（急カーブで強く減速）
        speed_factor = max(0.3, 1.0 - abs(error)/10)
        left_speed = int((BASE_SPEED - turn) * speed_factor)
        right_speed = int((BASE_SPEED + turn) * speed_factor)

        set_motors(left_speed, right_speed)
        
        # テレメトリ送信（定期的に）
        if time.ticks_diff(current_time, last_telemetry_time) > TELEMETRY_INTERVAL_MS:
            last_telemetry_time = current_time
            led.toggle()
            send_telemetry()
            print(f"送信 | センサー: {values} | L:{current_left_speed} R:{current_right_speed} | エラー:{error:.2f}")
        
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("\n=== 割り込み検出 ===")

finally:
    stop_motors()
    led.value(0)
    wlan.disconnect()
    wlan.active(False)
    print("=== プログラム終了 ===")

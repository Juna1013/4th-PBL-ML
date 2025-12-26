'''
ライントレース + WiFi通信版
test_01.pyのライントレースロジックにWiFi通信機能のみを追加
'''

from machine import Pin, PWM
import network
import time
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

# WiFi/テレメトリ設定
TELEMETRY_INTERVAL_MS = 500
TELEMETRY_URL = config.API_URL
REQUEST_TIMEOUT = 5

# グローバル変数（テレメトリ用）
wlan = None
current_sensor_values = [0] * 8
current_left_speed = 0
current_right_speed = 0
current_error = 0
current_turn = 0

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

# WiFi接続関数
def connect_wifi():
    """WiFiに接続"""
    global wlan
    
    print("=" * 50)
    print("WiFi接続開始")
    print("=" * 50)
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print(f"接続中: {config.SSID}")
        wlan.connect(config.SSID, config.PASSWORD)
        
        timeout = 30
        while not wlan.isconnected() and timeout > 0:
            print(".", end="")
            time.sleep(1)
            timeout -= 1
            led.toggle()
        
        print()
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"✅ WiFi接続成功!")
        print(f"   IPアドレス: {ip}")
        print(f"   サーバー: {TELEMETRY_URL}")
        led.value(1)
        return True
    else:
        print("❌ WiFi接続失敗")
        led.value(0)
        return False

# テレメトリ送信関数
def send_telemetry():
    """テレメトリデータを送信"""
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
        
        response = urequests.post(
            TELEMETRY_URL,
            data=json_data,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        status = response.status_code
        response.close()
        gc.collect()
        
        return status == 200
        
    except Exception as e:
        print(f"❌ テレメトリ送信エラー: {e}")
        return False

# モーター制御関数（test_01.pyと同じ）
def set_motors(left_duty, right_duty):
    global current_left_speed, current_right_speed
    
    left_duty = int(left_duty * LEFT_MOTOR_CORRECTION)
    right_duty = int(right_duty * RIGHT_MOTOR_CORRECTION)

    # PWM範囲に制限（ゼロ許容）
    left_duty = max(0, min(65535, left_duty))
    right_duty = max(0, min(65535, right_duty))
    
    # グローバル変数に保存（テレメトリ用）
    current_left_speed = left_duty
    current_right_speed = right_duty

    left_fwd.duty_u16(left_duty)
    left_rev.duty_u16(0)

    right_fwd.duty_u16(0)
    right_rev.duty_u16(right_duty)

def stop_motors():
    for pwm in [left_fwd, left_rev, right_fwd, right_rev]:
        pwm.duty_u16(0)
    print("=== モーター停止 ===")

# メインプログラム
def main():
    global current_sensor_values, current_error, current_turn
    
    print("=" * 50)
    print("ライントレース + WiFi通信版")
    print("=" * 50)
    
    # WiFi接続
    if not connect_wifi():
        print("WiFi接続をスキップして、ライントレースのみ実行します。")
    
    print("=" * 50)
    print("=== ライントレース開始（改良版） ===")
    print("   (Ctrl+C で停止)")
    print("=" * 50)
    
    last_error = 0
    last_debug_time = 0
    last_telemetry_time = 0
    telemetry_success_count = 0
    telemetry_fail_count = 0
    
    try:
        while True:
            # センサー読み取り（test_01.pyと同じ）
            values = [s.value() for s in sensors]
            current_sensor_values = values
            
            current_time = time.ticks_ms()
            
            # デバッグ表示（test_01.pyと同じ）
            if time.ticks_diff(current_time, last_debug_time) > 500:
                last_debug_time = current_time
                led.toggle()
                print("センサー状態:", " ".join(str(v) for v in values))
            
            # 誤差計算（test_01.pyと同じ）
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
            
            # PD制御（test_01.pyと同じ）
            error_diff = error - last_error
            turn = int(KP * error + KD * error_diff)
            last_error = error
            current_turn = turn
            
            # ターン量を制限（test_01.pyと同じ）
            turn = max(-BASE_SPEED, min(BASE_SPEED, turn))
            
            # 誤差に応じて減速（test_01.pyと同じ）
            speed_factor = max(0.3, 1.0 - abs(error)/10)
            left_speed = int((BASE_SPEED - turn) * speed_factor)
            right_speed = int((BASE_SPEED + turn) * speed_factor)
            
            # モーター制御（test_01.pyと同じ）
            set_motors(left_speed, right_speed)
            
            # テレメトリ送信（追加機能）
            if wlan and wlan.isconnected() and time.ticks_diff(current_time, last_telemetry_time) > TELEMETRY_INTERVAL_MS:
                last_telemetry_time = current_time
                
                success = send_telemetry()
                if success:
                    telemetry_success_count += 1
                    print(f"📤 送信成功 [{telemetry_success_count}] | L:{current_left_speed} R:{current_right_speed} | エラー:{current_error:.2f}")
                else:
                    telemetry_fail_count += 1
                    print(f"⚠️  送信失敗 [{telemetry_fail_count}]")
            
            time.sleep_ms(10)
    
    except KeyboardInterrupt:
        print("\n=== 割り込み検出 ===")
    
    finally:
        stop_motors()
        led.value(0)
        if wlan:
            wlan.disconnect()
            wlan.active(False)
        
        print("\n" + "=" * 50)
        print("📊 統計情報")
        print(f"   送信成功: {telemetry_success_count}")
        print(f"   送信失敗: {telemetry_fail_count}")
        print("=" * 50)
        print("=== プログラム終了 ===")

# プログラム実行
if __name__ == "__main__":
    main()

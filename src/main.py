'''
ライントレース + テレメトリ送信プログラム（統合版）
- PD制御によるライントレース
- リアルタイムテレメトリ送信
- 堅牢なエラーハンドリング
- メモリ管理
'''

from machine import Pin, PWM
import network
import time
import urequests
import ujson
import gc
import config

# ============================================================
# ピン定義
# ============================================================
LEFT_FWD_PIN = 5
LEFT_REV_PIN = 4
RIGHT_FWD_PIN = 2
RIGHT_REV_PIN = 3

SENSOR_PINS = [22, 21, 28, 27, 26, 18, 17, 16]
LED_PIN = "LED"

# ============================================================
# 走行パラメータ
# ============================================================
BASE_SPEED = 8000
LEFT_MOTOR_CORRECTION = 0.77
RIGHT_MOTOR_CORRECTION = 1.0

# ライントレース制御パラメータ
KP = 9000
KD = 3000
WEIGHTS = [-7, -5, -3, -1, 1, 3, 5, 7]

# ============================================================
# テレメトリ送信設定
# ============================================================
TELEMETRY_INTERVAL_MS = 500  # 500msごとに送信
TELEMETRY_URL = config.API_URL
REQUEST_TIMEOUT = 5  # タイムアウト（秒）

# ============================================================
# グローバル変数
# ============================================================
# モーター・センサー状態
current_left_speed = 0
current_right_speed = 0
current_sensor_values = [0] * 8
current_error = 0
current_turn = 0

# ハードウェア
wlan = None
sensors = []
left_fwd = None
left_rev = None
right_fwd = None
right_rev = None
led = None

# ============================================================
# WiFi接続関数
# ============================================================
def connect_wifi():
    """WiFiに接続（タイムアウト付き）"""
    global wlan
    
    print("=" * 50)
    print("WiFi接続開始")
    print("=" * 50)
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print(f"接続中: {config.SSID}")
        wlan.connect(config.SSID, config.PASSWORD)
        
        # 接続を最大30秒待機
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

# ============================================================
# ハードウェア初期化
# ============================================================
def init_hardware():
    """モーター、センサー、LEDを初期化"""
    global sensors, left_fwd, left_rev, right_fwd, right_rev, led
    
    print("\nハードウェア初期化中...")
    
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
    led.value(0)
    
    print("✅ ハードウェア初期化完了\n")

# ============================================================
# モーター制御関数
# ============================================================
def set_motors(left_duty, right_duty):
    """モーター速度を設定"""
    global current_left_speed, current_right_speed
    
    # モーター補正適用
    left_duty = int(left_duty * LEFT_MOTOR_CORRECTION)
    right_duty = int(right_duty * RIGHT_MOTOR_CORRECTION)

    # PWM範囲に制限
    left_duty = max(0, min(65535, left_duty))
    right_duty = max(0, min(65535, right_duty))
    
    # グローバル変数に保存
    current_left_speed = left_duty
    current_right_speed = right_duty

    # モーター駆動
    left_fwd.duty_u16(left_duty)
    left_rev.duty_u16(0)
    right_fwd.duty_u16(0)
    right_rev.duty_u16(right_duty)

def stop_motors():
    """モーターを停止"""
    global current_left_speed, current_right_speed
    for pwm in [left_fwd, left_rev, right_fwd, right_rev]:
        pwm.duty_u16(0)
    current_left_speed = 0
    current_right_speed = 0
    print("🛑 モーター停止")

# ============================================================
# センサーデータ取得
# ============================================================
def read_sensors():
    """センサー値を読み取り、グローバル変数に保存"""
    global current_sensor_values
    current_sensor_values = [s.value() for s in sensors]
    return current_sensor_values

# ============================================================
# テレメトリ送信関数
# ============================================================
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
        
        response = urequests.post(
            TELEMETRY_URL,
            data=json_data,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        status = response.status_code
        response.close()
        gc.collect()  # メモリ解放
        
        return status == 200
        
    except Exception as e:
        print(f"❌ テレメトリ送信エラー: {e}")
        return False

# ============================================================
# ライントレース制御
# ============================================================
def calculate_line_error(values):
    """センサー値から誤差を計算"""
    detected_count = 0
    weighted_sum = 0.0
    
    for i in range(8):
        if values[i] == 0:  # 黒ライン検出
            weighted_sum += WEIGHTS[i]
            detected_count += 1
    
    if detected_count == 0:
        return None  # ライン未検出
    else:
        return -(weighted_sum / detected_count)

def line_trace_step(last_error):
    """1ステップのライントレース処理"""
    global current_error, current_turn
    
    # センサー読み取り
    values = read_sensors()
    
    # 誤差計算
    error = calculate_line_error(values)
    if error is None:
        error = last_error  # ライン未検出時は前回の誤差を使用
    
    current_error = error
    
    # PD制御
    error_diff = error - last_error
    turn = int(KP * error + KD * error_diff)
    current_turn = turn
    
    # ターン量を制限
    turn = max(-BASE_SPEED, min(BASE_SPEED, turn))
    
    # 誤差に応じて減速（急カーブで強く減速）
    speed_factor = max(0.3, 1.0 - abs(error)/10)
    left_speed = int((BASE_SPEED - turn) * speed_factor)
    right_speed = int((BASE_SPEED + turn) * speed_factor)
    
    set_motors(left_speed, right_speed)
    
    return error

# ============================================================
# メインプログラム
# ============================================================
def main():
    print("=" * 50)
    print("ライントレース + テレメトリ送信（統合版）")
    print("=" * 50)
    
    # ハードウェア初期化
    init_hardware()
    
    # WiFi接続
    if not connect_wifi():
        print("WiFi接続が必要です。プログラムを終了します。")
        return
    
    print("=" * 50)
    print("🚗 ライントレース開始")
    print("   (Ctrl+C で停止)")
    print("=" * 50)
    
    last_error = 0
    last_telemetry_time = 0
    telemetry_success_count = 0
    telemetry_fail_count = 0
    
    try:
        while True:
            current_time = time.ticks_ms()
            
            # ライントレース制御
            last_error = line_trace_step(last_error)
            
            # テレメトリ送信（定期的に）
            if time.ticks_diff(current_time, last_telemetry_time) > TELEMETRY_INTERVAL_MS:
                last_telemetry_time = current_time
                led.toggle()
                
                success = send_telemetry()
                if success:
                    telemetry_success_count += 1
                    print(f"📤 送信成功 [{telemetry_success_count}] | センサー: {current_sensor_values} | L:{current_left_speed} R:{current_right_speed} | エラー:{current_error:.2f}")
                else:
                    telemetry_fail_count += 1
                    print(f"⚠️  送信失敗 [{telemetry_fail_count}]")
            
            time.sleep_ms(10)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  割り込み検出")
    
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
        print("プログラム終了")
        print("=" * 50)

# プログラム実行
if __name__ == "__main__":
    main()

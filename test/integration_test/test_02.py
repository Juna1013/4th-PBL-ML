from machine import Pin
import time
import network
import urequests
import ujson
import gc
import config

# ピン定義
SENSOR_PINS = [22, 21, 28, 27, 26, 18, 17, 16]
LED_PIN = "LED"

# WiFi/テレメトリ設定
TELEMETRY_INTERVAL_MS = 500  # 500msごとに送信
TELEMETRY_URL = config.API_URL

print("=" * 50)
print("センサーデータ収集プログラム")
print("手動でコースをなぞってください")
print("=" * 50)

# WiFi接続
print("\nWiFi接続中...")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config.SSID, config.PASSWORD)

# 最大10秒待機
timeout = 20
while not wlan.isconnected() and timeout > 0:
    print(".", end="")
    time.sleep(0.5)
    timeout -= 1

print()
if wlan.isconnected():
    print(f"✅ WiFi接続成功!")
    print(f"   IPアドレス: {wlan.ifconfig()[0]}")
    print(f"   サーバー: {TELEMETRY_URL}")
else:
    print("❌ WiFi接続失敗")
    print("プログラムを終了します")
    import sys
    sys.exit()

# センサー初期化
sensors = [Pin(p, Pin.IN, Pin.PULL_UP) for p in SENSOR_PINS]

# LED初期化
led = Pin(LED_PIN, Pin.OUT)
led.value(1)

# テレメトリ送信関数
def send_telemetry(sensor_values):
    """センサーデータをサーバーに送信"""
    try:
        gc.collect()
        
        data = {
            "timestamp": time.ticks_ms(),
            "sensors": sensor_values,
            "sensor_binary": "".join(str(v) for v in sensor_values)
        }
        
        json_data = ujson.dumps(data)
        headers = {'Content-Type': 'application/json'}
        
        response = urequests.post(
            TELEMETRY_URL,
            data=json_data,
            headers=headers,
            timeout=3
        )
        
        status = response.status_code
        response.close()
        
        del json_data
        del data
        gc.collect()
        
        return status == 200
        
    except Exception as e:
        return False

print("\n" + "=" * 50)
print("データ収集開始")
print("  手動でライントレースカーを動かしてください")
print("  Ctrl+C で停止")
print("=" * 50 + "\n")

last_telemetry_time = 0
success_count = 0
fail_count = 0
last_wifi_status = "-"

try:
    while True:
        # センサー読み取り
        values = [s.value() for s in sensors]
        
        current_time = time.ticks_ms()
        
        # センサー状態を表示（500msごと）
        if time.ticks_diff(current_time, last_telemetry_time) > 500:
            print(f"センサー: {' '.join(str(v) for v in values)} | WiFi: {last_wifi_status}")
        
        # テレメトリ送信
        if wlan.isconnected() and time.ticks_diff(current_time, last_telemetry_time) > TELEMETRY_INTERVAL_MS:
            last_telemetry_time = current_time
            led.toggle()
            
            if send_telemetry(values):
                success_count += 1
                last_wifi_status = "✓"
            else:
                fail_count += 1
                last_wifi_status = "✗"
        
        time.sleep_ms(50)  # CPU負荷軽減

except KeyboardInterrupt:
    print("\n\n" + "=" * 50)
    print("データ収集終了")
    print("=" * 50)

finally:
    led.value(0)
    if wlan:
        wlan.disconnect()
        wlan.active(False)
    
    print("\n📊 統計情報")
    print(f"   送信成功: {success_count}")
    print(f"   送信失敗: {fail_count}")
    print(f"   合計: {success_count + fail_count}")
    if (success_count + fail_count) > 0:
        success_rate = (success_count / (success_count + fail_count)) * 100
        print(f"   成功率: {success_rate:.1f}%")
    print("=" * 50)
    print("プログラム終了")

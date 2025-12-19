import network
import urequests
import ujson
import time
from machine import Pin
import gc

# Wi-Fi設定
WIFI_SSID = "YOUR_WIFI_SSID"  # Wi-FiのSSIDに変更してください
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"  # Wi-Fiのパスワードに変更してください

# エンドポイント設定
API_ENDPOINT = "http://example.com/api/sensor-data"  # 送信先のURLに変更してください

# センサーピン設定 
# センサーピン（8chデジタルセンサー）
SENSOR_PINS = [22, 21, 28, 27, 26, 18, 17, 16]
sensors = [Pin(p, Pin.IN, Pin.PULL_UP) for p in SENSOR_PINS]

# LED（接続確認用）
led = Pin("LED", Pin.OUT)

# Wi-Fi接続関数
def connect_wifi():
    """Wi-Fiに接続する"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print(f"Wi-Fiに接続中: {WIFI_SSID}")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        # 接続を最大30秒待機
        timeout = 30
        while not wlan.isconnected() and timeout > 0:
            print(".", end="")
            time.sleep(1)
            timeout -= 1
            led.toggle()
        
        print()
    
    if wlan.isconnected():
        print("✅ Wi-Fi接続成功!")
        print(f"   IPアドレス: {wlan.ifconfig()[0]}")
        led.value(1)
        return wlan
    else:
        print("❌ Wi-Fi接続失敗")
        led.value(0)
        return None

# センサーデータ取得関数
def get_sensor_data():
    """センサーの現在値を取得"""
    values = [s.value() for s in sensors]
    
    # 黒ライン検出カウント
    black_count = sum(1 for v in values if v == 0)
    
    return {
        "timestamp": time.time(),
        "sensor_values": values,
        "black_detected": black_count,
        "sensor_binary": "".join(str(v) for v in values)  # 例: "11100011"
    }

# データ送信関数
def send_data(data):
    """データをHTTP POSTで送信"""
    try:
        headers = {"Content-Type": "application/json"}
        json_data = ujson.dumps(data)
        
        print(f"📤 データ送信中: {json_data}")
        
        response = urequests.post(
            API_ENDPOINT,
            data=json_data,
            headers=headers,
            timeout=5
        )
        
        print(f"✅ 送信成功 (ステータス: {response.status_code})")
        print(f"   レスポンス: {response.text}")
        
        response.close()
        gc.collect()  # メモリ解放
        return True
        
    except Exception as e:
        print(f"❌ 送信エラー: {e}")
        return False

# メインプログラム
def main():
    print("=" * 50)
    print("Raspberry Pi Pico W - データ送信プログラム")
    print("=" * 50)
    
    # Wi-Fi接続
    wlan = connect_wifi()
    if not wlan:
        print("Wi-Fi接続が必要です。プログラムを終了します。")
        return
    
    print("\n📡 データ送信を開始します...")
    print("   (Ctrl+C で停止)\n")
    
    send_interval = 2  # 送信間隔（秒）
    
    try:
        while True:
            # センサーデータ取得
            sensor_data = get_sensor_data()
            
            # データ送信
            success = send_data(sensor_data)
            
            if success:
                led.toggle()
            
            # 次の送信まで待機
            time.sleep(send_interval)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  プログラムを停止しました")
    
    finally:
        led.value(0)
        print("=" * 50)
        print("プログラム終了")
        print("=" * 50)

# プログラム実行
if __name__ == "__main__":
    main()

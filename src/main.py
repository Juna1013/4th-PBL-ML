import time
from machine import Pin
import config

# モジュールをインポート
from network_manager import NetworkManager
from telemetry import TelemetryClient
from line_tracer import LineTracer

# ============================================================
# 設定
# ============================================================
# ピン定義
PIN_CONFIG = {
    'sensor_pins': [22, 21, 28, 27, 26, 18, 17, 16],
    'left_fwd_pin': 5,
    'left_rev_pin': 4,
    'right_fwd_pin': 2,
    'right_rev_pin': 3,
}

# 走行パラメータ
TRACER_CONFIG = {
    **PIN_CONFIG,
    'base_speed': 8000,
    'left_correction': 0.77,
    'right_correction': 1.0,
    'kp': 9000,
    'kd': 3000,
    'weights': [-7, -5, -3, -1, 1, 3, 5, 7],
}

# テレメトリ設定
TELEMETRY_INTERVAL_MS = 500  # 500msごとに送信
TELEMETRY_URL = f"http://{config.SERVER_IP}:8000/telemetry"

# ============================================================
# メインプログラム
# ============================================================
def main():
    print("=" * 50)
    print("ライントレース + テレメトリ送信（リファクタリング版）")
    print("=" * 50)
    
    # LED初期化（状態表示用）
    led = Pin("LED", Pin.OUT)
    led.value(0)
    
    # ネットワークマネージャー初期化
    print("\n📡 ネットワーク初期化中...")
    network_mgr = NetworkManager(
        ssid=config.SSID,
        password=config.PASSWORD,
        led_pin="LED"
    )
    
    # WiFi接続
    if not network_mgr.connect():
        print("❌ WiFi接続が必要です。プログラムを終了します。")
        return
    
    print(f"   サーバー: {TELEMETRY_URL}\n")
    
    # ライントレーサー初期化
    print("🚗 ライントレーサー初期化中...")
    tracer = LineTracer(TRACER_CONFIG)
    
    # テレメトリクライアント初期化
    print("📊 テレメトリクライアント初期化中...")
    telemetry = TelemetryClient(TELEMETRY_URL)
    
    print("\n" + "=" * 50)
    print("🚀 ライントレース開始")
    print("   (Ctrl+C で停止)")
    print("=" * 50)
    
    last_telemetry_time = 0
    
    try:
        while True:
            current_time = time.ticks_ms()
            
            # ライントレース制御（1ステップ）
            tracer.step()
            
            # テレメトリ送信（定期的に）
            if time.ticks_diff(current_time, last_telemetry_time) > TELEMETRY_INTERVAL_MS:
                last_telemetry_time = current_time
                led.toggle()
                
                # 現在の状態を取得
                state = tracer.get_state()
                
                # テレメトリ送信
                success = telemetry.send(
                    sensor_values=state['sensors'],
                    motor_left=state['motor_left'],
                    motor_right=state['motor_right'],
                    error=state['error'],
                    turn=state['turn'],
                    base_speed=state['base_speed'],
                    network_manager=network_mgr
                )
                
                # ログ出力
                if success:
                    stats = telemetry.get_stats()
                    print(f"📤 送信成功 [{stats['success']}] | センサー: {state['sensors']} | L:{state['motor_left']} R:{state['motor_right']} | エラー:{state['error']:.2f}")
                else:
                    stats = telemetry.get_stats()
                    print(f"⚠️  送信失敗 [{stats['fail']}]")
            
            time.sleep_ms(10)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  割り込み検出")
    
    finally:
        # クリーンアップ
        tracer.stop()
        led.value(0)
        network_mgr.disconnect()
        
        # 統計情報表示
        stats = telemetry.get_stats()
        print("\n" + "=" * 50)
        print("📊 統計情報")
        print(f"   送信成功: {stats['success']}")
        print(f"   送信失敗: {stats['fail']}")
        print(f"   合計: {stats['total']}")
        if stats['total'] > 0:
            success_rate = (stats['success'] / stats['total']) * 100
            print(f"   成功率: {success_rate:.1f}%")
        print("=" * 50)
        print("プログラム終了")
        print("=" * 50)

# プログラム実行
if __name__ == "__main__":
    main()

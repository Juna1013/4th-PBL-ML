from machine import Pin
import time

# --- フォトリフレクタの接続ピン ---
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]

# --- Pico WのデフォルトLEDを設定 ---
led = Pin("LED", Pin.OUT)

# --- センサー初期化（プルなし） ---
# フォトリフレクタモジュールに抵抗が内蔵されている場合はプル不要
sensors = [Pin(p, Pin.IN) for p in PHOTOREFLECTOR_PINS]

print("=== ライントレースセンサー テスト開始 ===")
print("プル抵抗: なし（モジュール内蔵抵抗を使用）")
print("各センサーの値を個別に表示します")
print("LEDが点滅中は動作中です。Ctrl + C で停止できます。\n")

try:
    count = 0
    while True:
        count += 1
        # LEDを0.5秒ごとに点滅
        led.value(count % 2)
        
        # センサー値を読み取り
        values = [s.value() for s in sensors]
        
        # 詳細表示
        print(f"\n--- 読み取り {count} ---")
        print("センサー状態:", " ".join(str(v) for v in values))
        
        # 各センサーを個別に表示
        for i, v in enumerate(values):
            status = "黒" if v == 0 else "白"
            print(f"  S{i} (GP{PHOTOREFLECTOR_PINS[i]}): {v} ({status})")
        
        time.sleep(0.5)

except KeyboardInterrupt:
    led.value(0)  # 終了時にLEDを消灯
    print("\n=== テスト終了 ===")

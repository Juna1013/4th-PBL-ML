from machine import Pin
import time

# --- フォトリフレクタの接続ピン ---
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]

# --- LED設定 ---
# Pico Wの場合は 'LED' で指定可能（GPIO25に内部で接続されている）
led = Pin("LED", Pin.OUT)
led.value(1)  # 実行開始と同時に点灯

# --- センサー初期化 ---
sensors = [Pin(p, Pin.IN) for p in PHOTOREFLECTOR_PINS]

print("=== ライントレースセンサー テスト開始 ===")
print("黒線: 0, 白地: 1")
print("Ctrl + C で停止します\n")

try:
    while True:
        values = [s.value() for s in sensors]
        print("センサー状態:", " ".join(str(v) for v in values))
        time.sleep(0.2)

except KeyboardInterrupt:
    led.value(0)  # 終了時にLEDを消灯
    print("\n=== テスト終了 ===")

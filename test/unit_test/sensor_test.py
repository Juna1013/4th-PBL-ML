from machine import Pin
import time

# --- フォトリフレクタの接続ピン ---
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]

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
    print("\n=== テスト終了 ===")

from machine import Pin
import time

# Pinの設定
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]

# センサーの初期化
sensors = [Pin(p, Pin.IN) for p in PHOTOREFLECTOR_PINS]

try:
    while True:
        values = [s.value() for s in sensors]
        # 0: 黒線検出（LED点灯）
        # 1: 白地（LED消灯）
        print("センサー状態:", " ".join(str(v) for v in values))
        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nテスト終了")

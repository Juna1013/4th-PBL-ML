from machine import Pin
import time

# --- フォトリフレクタの接続ピン ---
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]

# --- Pico WのデフォルトLEDを設定 ---
led = Pin("LED", Pin.OUT)

# --- センサー初期化 ---
sensors = [Pin(p, Pin.IN) for p in PHOTOREFLECTOR_PINS]

print("=== ライントレースセンサー テスト開始 ===")
print("LEDが点滅中は動作中です。Ctrl + C で停止できます。\n")

try:
    while True:
        # LEDを1秒ごとに点滅
        led.value(1)
        values = [s.value() for s in sensors]
        print("センサー状態:", " ".join(str(v) for v in values))
        time.sleep(1)

        led.value(0)
        values = [s.value() for s in sensors]
        print("センサー状態:", " ".join(str(v) for v in values))
        time.sleep(1)

except KeyboardInterrupt:
    led.value(0)  # 終了時にLEDを消灯
    print("\n=== テスト終了 ===")

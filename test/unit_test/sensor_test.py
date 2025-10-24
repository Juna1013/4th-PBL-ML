from machine import Pin
import time

# --- 設定 ---
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]
BUTTON_PIN = 15  # ← BOOTSELの代わりに使うボタンGPIO

# --- 初期化 ---
sensors = [Pin(p, Pin.IN) for p in PHOTOREFLECTOR_PINS]
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)  # 押すとGNDに落ちる構成

running = False  # センサー読み取りON/OFF状態
last_button_state = 1

print("ボタンでON/OFFを切り替えます。")

try:
    while True:
        current_state = button.value()

        # ボタンが押された瞬間（立ち下がり検出）
        if last_button_state == 1 and current_state == 0:
            running = not running
            print("▶ センサー測定" if running else "■ 停止")
            time.sleep(0.3)  # チャタリング防止

        last_button_state = current_state

        # 測定中のみセンサー値を表示
        if running:
            values = [s.value() for s in sensors]
            print("センサー状態:", " ".join(str(v) for v in values))
            time.sleep(0.2)

except KeyboardInterrupt:
    print("\n終了します。")

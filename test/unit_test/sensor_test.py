from machine import Pin
import time

# =====================================================
# 実際の回路配線に基づくピン定義
# =====================================================

# --- センサー接続ピン（デジタル入力） ---
# AE-NJL5901AR-8ch フォトリフレクタアレイ
# 実際の配線（センサー1-8の順）:
# 1:GP22, 2:GP21, 3:GP28, 4:GP27, 5:GP26, 6:GP18, 7:GP17, 8:GP16
SENSOR_PINS = [22, 21, 28, 27, 26, 18, 17, 16]

# --- センサーの重み付け（8つのセンサー用） ---
# 左端(-3.5)から右端(+3.5)までの位置を表す
SENSOR_WEIGHTS = [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5]

# --- Pico WのデフォルトLEDを設定 ---
led = Pin("LED", Pin.OUT)

# --- センサー初期化（デジタル入力、プルアップ） ---
sensors = [Pin(p, Pin.IN, Pin.PULL_UP) for p in SENSOR_PINS]

print("=== ライントレースセンサー テスト開始（8chデジタル） ===")
print("【重要】センサー基板上のVR（半固定抵抗）で感度調整が必要です！")
print("  - 白い面上で全て1（□）になるように調整してください")
print("  - 黒いライン上で0（■）になるように調整してください")
print("  - 調整しないと常に同じ値になり、ライン検出できません\n")

try:
    count = 0
    
    while True:
        count += 1
        # LEDを点滅
        led.value(count % 2)
        
        # デジタルピンを読み取り（0=黒検出, 1=白検出）
        values = [s.value() for s in sensors]
        
        # シンプルな0, 1の出力表示
        print(' '.join(str(v) for v in values))
        
        time.sleep(0.5)

except KeyboardInterrupt:
    led.value(0)


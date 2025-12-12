from machine import Pin
import time

# =====================================================
# 実際の回路配線に基づくピン定義
# =====================================================

# --- センサー接続ピン（デジタル入力） ---
# AE-NJL5901AR-8ch フォトリフレクタアレイ
# 実際の配線: GP14, GP15, GP16, GP17, GP18, GP19, GP20, GP21
SENSOR_PINS = [14, 15, 16, 17, 18, 19, 20, 21]

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
        
        # ビジュアル表示（センサー0〜7を左から右へ）
        visual = ''.join(['■' if v == 0 else '□' for v in values])
        
        # 出力表示
        print(f"読み取り {count}: {visual}")
        print("センサー: " + " ".join([f"S{i}" for i in range(8)]))
        print("値:       " + " ".join(f" {v}" for v in values))
        
        # 黒ライン検出の判定と誤差計算
        black_sensors = [i for i, v in enumerate(values) if v == 0]
        if black_sensors:
            detected_weights = [SENSOR_WEIGHTS[i] for i in black_sensors]
            weighted_sum = sum(detected_weights)
            error = -(weighted_sum / len(detected_weights))
            sensors_str = ','.join([f"S{i}" for i in black_sensors])
            print(f"黒検出: [{sensors_str}] | 誤差: {error:+.2f}")
        else:
            print("黒検出: なし（ラインロスト）")
        
        print()
        time.sleep(0.5)

except KeyboardInterrupt:
    led.value(0)
    print("\n=== テスト終了 ===")



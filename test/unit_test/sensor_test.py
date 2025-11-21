from machine import Pin
import time

# --- フォトリフレクタの接続ピン ---
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]

# --- センサーの重み付け（ハードウェアマニュアルに基づく） ---
SENSOR_WEIGHTS = [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5]

# --- Pico WのデフォルトLEDを設定 ---
led = Pin("LED", Pin.OUT)

# --- センサー初期化（プルなし） ---
# フォトリフレクタモジュールに抵抗が内蔵されている場合はプル不要
sensors = [Pin(p, Pin.IN) for p in PHOTOREFLECTOR_PINS]

print("=== ライントレースセンサー テスト開始 ===")
print("プル抵抗: なし（モジュール内蔵抵抗を使用）")
print("センサー配置（左から右へ）:")
print("  S0(GP16) S1(GP17) S2(GP18) S3(GP19) S4(GP20) S5(GP21) S6(GP22) S7(GP28)")
print("  Weight: -3.5, -2.5, -1.5, -0.5, +0.5, +1.5, +2.5, +3.5")
print("LEDが点滅中は動作中です。Ctrl + C で停止できます。\n")

try:
    count = 0
    while True:
        count += 1
        # LEDを0.5秒ごとに点滅
        led.value(count % 2)
        
        # センサー値を読み取り
        values = [s.value() for s in sensors]
        
        # ビジュアル表示（黒=■、白=□）
        visual = ''.join(['■' if v == 0 else '□' for v in values])
        
        # 詳細表示
        print(f"読み取り {count}: {visual}")
        print("値:     " + " ".join(str(v) for v in values))
        
        # 黒ライン検出センサーの情報
        detected_indices = [i for i, v in enumerate(values) if v == 0]
        if detected_indices:
            detected_weights = [SENSOR_WEIGHTS[i] for i in detected_indices]
            weighted_sum = sum(detected_weights)
            error = -(weighted_sum / len(detected_weights))
            print(f"黒検出: S{detected_indices} | 重み合計: {weighted_sum:.1f} | 誤差: {error:+.2f}")
        else:
            print("黒検出: なし（ラインロスト状態）")
        
        # 各センサーを詳細表示
        print("詳細:")
        for i, v in enumerate(values):
            status = "黒" if v == 0 else "白"
            weight_str = f"({SENSOR_WEIGHTS[i]:+.1f})" if v == 0 else "     "
            print(f"  S{i} (GP{PHOTOREFLECTOR_PINS[i]:2d}): {v} ({status}) {weight_str}")
        
        print()  # 空行
        time.sleep(0.5)

except KeyboardInterrupt:
    led.value(0)  # 終了時にLEDを消灯
    print("\n=== テスト終了 ===")

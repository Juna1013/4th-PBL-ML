from machine import Pin
import time

# --- フォトリフレクタの接続ピン ---
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]

# --- センサーの重み付け（ハードウェアマニュアルに基づく） ---
SENSOR_WEIGHTS = [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5]

# --- Pico WのデフォルトLEDを設定 ---
led = Pin("LED", Pin.OUT)

# --- センサー初期化 ---
sensors = [Pin(p, Pin.IN) for p in PHOTOREFLECTOR_PINS]

print("=== ライントレースセンサー 診断テスト ===")
print("\n【問題の診断】")
print("症状: 電源ON時は全て1、電源OFF時は全て黒(0)になる")
print("原因の可能性:")
print("  1. センサー電源が接続されていない")
print("  2. センサーモジュールの電源ライン不良")
print("  3. GND接続不良")
print("  4. ピン配置が異なる可能性")
print("\n診断開始...")
time.sleep(2)

try:
    count = 0
    prev_values = None
    constant_count = 0
    
    while True:
        count += 1
        # LEDを点滅
        led.value(count % 2)
        
        # センサー値を読み取り
        values = [s.value() for s in sensors]
        
        # ビジュアル表示
        visual = ''.join(['■' if v == 0 else '□' for v in values])
        
        print(f"\n読み取り {count}: {visual}")
        print("値:     " + " ".join(str(v) for v in values))
        
        # 変化検出
        if prev_values is not None and prev_values == values:
            constant_count += 1
        else:
            constant_count = 0
        
        prev_values = values
        
        # 診断情報
        all_ones = all(v == 1 for v in values)
        all_zeros = all(v == 0 for v in values)
        
        if all_ones:
            print("⚠️  【警告】全て1（白）です")
            print("   → センサー電源が正常に供給されていない可能性があります")
            if constant_count > 5:
                print("   → 値が変わらない場合、配線を確認してください")
        elif all_zeros:
            print("⚠️  【警告】全て0（黒）です")
            print("   → 以下のいずれかの問題が考えられます:")
            print("     • センサーの赤外線LED不点灯")
            print("     • 出力ピンの不良")
            if constant_count > 5:
                print("   → 値が変わらない場合、センサーモジュール本体の不良かもしれません")
        else:
            # 部分的に検出している
            black_sensors = [i for i, v in enumerate(values) if v == 0]
            white_sensors = [i for i, v in enumerate(values) if v == 1]
            print(f"✓ 黒検出センサー: S{black_sensors}")
            print(f"✓ 白検出センサー: S{white_sensors}")
            
            # 誤差計算
            if black_sensors:
                detected_weights = [SENSOR_WEIGHTS[i] for i in black_sensors]
                weighted_sum = sum(detected_weights)
                error = -(weighted_sum / len(detected_weights))
                print(f"  誤差計算: {error:+.2f}")
        
        # センサーの詳細情報
        if count % 5 == 1:  # 5読み取りごとに詳細表示
            print("\n【詳細情報】")
            for i, v in enumerate(values):
                status = "黒" if v == 0 else "白"
                print(f"  S{i} (GP{PHOTOREFLECTOR_PINS[i]:2d}): {v} ({status})")
        
        time.sleep(0.5)

except KeyboardInterrupt:
    led.value(0)
    print("\n\n=== テスト終了 ===")
    print("\n【診断結果】")
    if prev_values:
        if all(v == 1 for v in prev_values):
            print("💡 全て1が続く場合:")
            print("   1. センサーの電源ケーブルを確認してください")
            print("   2. 赤外線LED（通常は赤い光）が点灯しているか確認")
            print("   3. モジュールの3.3V/GND接続を再確認")
        elif all(v == 0 for v in prev_values):
            print("💡 全て0が続く場合:")
            print("   1. 出力ピンの配線を確認してください")
            print("   2. Pico Wのピン番号を再確認: [16, 17, 18, 19, 20, 21, 22, 28]")
            print("   3. センサーモジュールのカットポジションを確認")
        else:
            print("✓ センサーは正常に動作しています")
            print("  ラインの位置を変更して、誤差計算が変わることを確認してください")

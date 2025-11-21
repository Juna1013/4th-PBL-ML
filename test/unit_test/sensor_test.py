from machine import Pin, ADC
import time

# --- フォトリフレクタの接続ピン ---
# デジタルピン: 16, 17, 18, 21, 22
# アナログピン: 26(ADC0), 27(ADC1), 28(ADC2)
DIGITAL_PINS = [16, 17, 18, 21, 22]
ANALOG_PINS = [26, 27, 28]  # これらはADCで読む必要がある

# --- センサーの重み付け（ハードウェアマニュアルに基づく） ---
SENSOR_WEIGHTS = [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5]

# --- Pico WのデフォルトLEDを設定 ---
led = Pin("LED", Pin.OUT)

# --- センサー初期化 ---
# デジタルピンはPin.INで初期化
digital_sensors = [Pin(p, Pin.IN) for p in DIGITAL_PINS]

# アナログピンはADCで初期化（アナログ値を0-1で正規化）
adc_sensors = [ADC(Pin(p)) for p in ANALOG_PINS]

# アナログ値の閾値（0-65535の範囲で、通常は32768程度が中点）
ADC_THRESHOLD = 32768  # 中点を基準に黒/白を判定

print("=== ライントレースセンサー 診断テスト（デジタル+アナログ対応） ===")
print(f"\nセンサー構成:")
print(f"  デジタルピン（GP）: {DIGITAL_PINS}")
print(f"  アナログピン（ADC）: {ANALOG_PINS}")
print(f"  アナログ閾値: {ADC_THRESHOLD}")
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
        # デジタルピンは直接0/1を読み取り
        digital_values = [s.value() for s in digital_sensors]
        
        # アナログピンはADCで読み取り、閾値で0/1に変換
        analog_values = []
        for adc in adc_sensors:
            raw_adc = adc.read_u16()  # 0-65535の値
            # 高い値=白（反射している）、低い値=黒（反射していない）
            analog_values.append(0 if raw_adc < ADC_THRESHOLD else 1)
        
        # 全センサー値を結合（デジタル5個 + アナログ3個 = 8個）
        values = digital_values + analog_values
        
        # ビジュアル表示
        visual = ''.join(['■' if v == 0 else '□' for v in values])
        
        print(f"\n読み取り {count}: {visual}")
        print("値:     " + " ".join(str(v) for v in values))
        print(f"詳細   (デジタル: {' '.join(str(v) for v in digital_values)}) + (アナログ: {' '.join(str(v) for v in analog_values)})")
        
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
            for i, v in enumerate(digital_values):
                status = "黒" if v == 0 else "白"
                print(f"  S{i} (デジタルGP{DIGITAL_PINS[i]:2d}): {v} ({status})")
            for i, (pin, adc, v) in enumerate(zip(ANALOG_PINS, adc_sensors, analog_values)):
                raw_val = adc.read_u16()
                status = "黒" if v == 0 else "白"
                print(f"  S{5+i} (アナログGP{pin:2d}, ADC{i}): {v} ({status}) [Raw: {raw_val}]")
        
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
            print("   2. Pico Wのピン番号を再確認:")
            print(f"      デジタル: {DIGITAL_PINS}")
            print(f"      アナログ: {ANALOG_PINS}")
            print("   3. センサーモジュールのカットポジションを確認")
        else:
            print("✓ センサーは正常に動作しています")
            print("  ラインの位置を変更して、誤差計算が変わることを確認してください")

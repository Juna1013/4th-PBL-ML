from machine import Pin, ADC
import time

# --- フォトリフレクタの接続ピン ---
# デジタルピン: 16, 17, 18, 21, 22
# アナログピン: 26(ADC0), 27(ADC1), 28(ADC2)
DIGITAL_PINS = [16, 17, 18, 21, 22]
ANALOG_PINS = [26, 27, 28]

# --- センサーの重み付け（ハードウェアマニュアルに基づく） ---
SENSOR_WEIGHTS = [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5]

# --- Pico WのデフォルトLEDを設定 ---
led = Pin("LED", Pin.OUT)

# --- センサー初期化 ---
digital_sensors = [Pin(p, Pin.IN) for p in DIGITAL_PINS]
adc_sensors = [ADC(Pin(p)) for p in ANALOG_PINS]

# アナログ値の閾値
ADC_THRESHOLD = 32768

print("=== ライントレースセンサー テスト開始 ===\n")

try:
    count = 0
    
    while True:
        count += 1
        # LEDを点滅
        led.value(count % 2)
        
        # センサー値を読み取り
        digital_values = [s.value() for s in digital_sensors]
        
        # アナログピンはADCで読み取り、閾値で0/1に変換
        analog_values = []
        for adc in adc_sensors:
            raw_adc = adc.read_u16()
            analog_values.append(0 if raw_adc < ADC_THRESHOLD else 1)
        
        # 全センサー値を結合
        values = digital_values + analog_values
        
        # ビジュアル表示
        visual = ''.join(['■' if v == 0 else '□' for v in values])
        
        # シンプルな出力
        print(f"読み取り {count}: {visual}")
        print("値:     " + " ".join(str(v) for v in values))
        
        # 黒ラインを検出したセンサー情報
        black_sensors = [i for i, v in enumerate(values) if v == 0]
        if black_sensors:
            detected_weights = [SENSOR_WEIGHTS[i] for i in black_sensors]
            weighted_sum = sum(detected_weights)
            error = -(weighted_sum / len(detected_weights))
            print(f"黒検出: S{black_sensors} | 誤差: {error:+.2f}")
        else:
            print("黒検出: なし（ラインロスト）")
        
        print()
        time.sleep(0.5)

except KeyboardInterrupt:
    led.value(0)
    print("\n=== テスト終了 ===")


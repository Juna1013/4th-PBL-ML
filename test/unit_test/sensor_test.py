from machine import Pin, ADC
import time

# --- フォトリフレクタの接続ピン（アナログのみ） ---
# アナログピン: 26(ADC0), 27(ADC1), 28(ADC2), 29(ADC3)
ANALOG_PINS = [26, 27, 28, 29]

# --- センサーの重み付け（ハードウェアマニュアルに基づく） ---
SENSOR_WEIGHTS = [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5]

# --- Pico WのデフォルトLEDを設定 ---
led = Pin("LED", Pin.OUT)

# --- センサー初期化（アナログのみ） ---
adc_sensors = [ADC(Pin(p)) for p in ANALOG_PINS]

# アナログ値の閾値
ADC_THRESHOLD = 32768

print("=== ライントレースセンサー テスト開始（アナログのみ） ===\n")

try:
    count = 0
    
    while True:
        count += 1
        # LEDを点滅
        led.value(count % 2)
        
        # アナログピンをADCで読み取り、閾値で0/1に変換
        values = []
        for adc in adc_sensors:
            raw_adc = adc.read_u16()
            values.append(0 if raw_adc < ADC_THRESHOLD else 1)
        
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



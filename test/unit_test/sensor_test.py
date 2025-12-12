from machine import ADC, Pin
import time

# =====================================================
# アナログピン設定
# =====================================================
adc_right = ADC(Pin(26))   # 右
adc_center = ADC(Pin(27))  # 中
adc_left = ADC(Pin(28))    # 左

# 閾値（これより大きいと「1:白」、小さいと「0:黒」）
THRESHOLD = 40000 

led = Pin("LED", Pin.OUT)

print("=== 3ch センサー出力 (左 中 右) ===")
print("1 = 白 (床), 0 = 黒 (ライン)")

try:
    while True:
        # 1. 値の読み取り
        val_l = adc_left.read_u16()
        val_c = adc_center.read_u16()
        val_r = adc_right.read_u16()
        
        # 2. 0か1に変換 (int(True)は1になります)
        # 閾値より大きければ「1(白)」、小さければ「0(黒)」
        res_l = 1 if val_l > THRESHOLD else 0
        res_c = 1 if val_c > THRESHOLD else 0
        res_r = 1 if val_r > THRESHOLD else 0
        
        # 3. シンプルに出力 (例: "1 0 1")
        print(f"{res_l} {res_c} {res_r}")
        
        led.toggle()
        time.sleep(0.1) # 高速に確認したい場合はここを短くしてください

except KeyboardInterrupt:
    led.value(0)
    print("\n終了")
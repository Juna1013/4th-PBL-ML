from machine import Pin, PWM
import time

# --- ピン定義 (単体テストから流用) ---
# 左モーター
LEFT_FWD_PIN = 5
LEFT_REV_PIN = 4
# 右モーター
RIGHT_FWD_PIN = 3
RIGHT_REV_PIN = 2
# フォトリフレクタ
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]
# LED
LED_PIN = "LED"


# --- 初期化 ---
print("ハードウェアを初期化中...")
# モーター
left_fwd = PWM(Pin(LEFT_FWD_PIN))
left_rev = PWM(Pin(LEFT_REV_PIN))
right_fwd = PWM(Pin(RIGHT_FWD_PIN))
right_rev = PWM(Pin(RIGHT_REV_PIN))
left_fwd.freq(1000)
left_rev.freq(1000)
right_fwd.freq(1000)
right_rev.freq(1000)

# センサー
sensors = [Pin(p, Pin.IN) for p in PHOTOREFLECTOR_PINS]

# LED
led = Pin(LED_PIN, Pin.OUT)


# --- モーター制御関数 ---
def set_motors(left_duty, right_duty):
    """ 
    左右のモーターのデューティ比を設定 (0-65535) 
    ライントレースは基本的に前進のため、REVピンは0に固定します。
    """
    
    # デューティ比を 0 〜 65535 の範囲に収める (クリッピング)
    left_duty = max(0, min(65535, int(left_duty)))
    right_duty = max(0, min(65535, int(right_duty)))
    
    # 前進方向にデューティ比を設定
    left_fwd.duty_u16(left_duty)
    left_rev.duty_u16(0)
    right_fwd.duty_u16(right_duty)
    right_rev.duty_u16(0)

def stop_motors():
    """ 両方のモーターを緊急停止 """
    left_fwd.duty_u16(0)
    left_rev.duty_u16(0)
    right_fwd.duty_u16(0)
    right_rev.duty_u16(0)
    print("=== モーター停止 ===")


# --- ライントレース パラメータ (ここを調整します) ---

# !! 重要: センサー値の仮定 !!
# 黒ライン = 1, 白地 = 0 と仮定します。
# もし逆 (黒=0, 白=1) の場合は、下の「※センサー値が逆の場合」のコメント行を有効にしてください。

# 制御パラメータ (要調整)
BASE_SPEED = 30000  # 基本速度 (0-65535)
KP = 8000           # 比例ゲイン (ズレをどれだけモーター出力に反映するか)

# センサーの重み付け (8個のセンサー用)
# [S0, S1, S2, S3, S4, S5, S6, S7]
# 左端 (マイナス) <-> 中央 (0) <-> 右端 (プラス)
WEIGHTS = [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5]


# --- メイン処理 ---
print("=== ライントレース 結合テスト開始 ===")
print("Ctrl + C で停止します。")
time.sleep(3) # 準備時間

try:
    led.value(1) # 動作中LED点灯
    
    while True:
        # 1. センサー値読み取り
        values = [s.value() for s in sensors]
        
        # ※センサー値が逆 (黒=0, 白=1) の場合は、以下のコメントを外してください
        # values = [1 - v for v in values] 

        # 2. ライン検出状態の確認
        line_detected_count = sum(values)

        if line_detected_count == 0:
            # --- ケース1: ラインロスト (全センサーが白) ---
            # 動作を停止 (または探索ルーチンへ)
            stop_motors()
            print(f"ラインロスト: {values}")
            # time.sleep(0.5) # 頻繁な再開を防ぐ
            # 停止したままにする場合は break 
        
        elif line_detected_count == 8:
            # --- ケース2: 全センサーが黒 (スタート/ゴールライン？) ---
            stop_motors()
            print(f"全センサー検出 (ゴール？): {values}")
            break # テスト終了

        else:
            # --- ケース3: ライン検出中 (P制御) ---
            
            # 3. エラー（ラインの中央からのズレ）を計算
            error = 0
            for i in range(8):
                error += WEIGHTS[i] * values[i]
            
            # 検出したセンサー数で割って平均化 (より安定した制御のため)
            error = error / line_detected_count 
            
            # 4. モーター出力計算 (P制御)
            # ズレ(error)に応じて左右のモーター出力を調整
            turn = KP * error
            
            left_speed = BASE_SPEED - turn
            right_speed = BASE_SPEED + turn
            
            # 5. モーター制御
            set_motors(left_speed, right_speed)
            
            # デバッグ情報 (必要に応じてコメントを外す)
            # print(f"V: {values} | Err: {error:.2f} | Turn: {turn:.0f} | L: {int(left_speed)} R: {int(right_speed)}")

        # ループ周期の調整 (処理が速すぎないように)
        time.sleep_ms(10)

except KeyboardInterrupt:
    # Ctrl + C が押されたら停止
    print("\n割り込み検出。")

finally:
    # 終了処理
    stop_motors()
    led.value(0) # LED消灯
    print("=== テスト終了 ===")

"""
スタンドアロンライントレースプログラム（8センサー重み付け制御版）
WiFi接続不要で、8個のフォトリフレクタで重み付けライントレース

使い方:
1. Pico Wにプログラムをアップロード
2. GPIO 16-22, 28に8個のフォトリフレクタを接続（左から右へ順番）
3. GPIO 2-5にモーター（MakerDrive）を接続
4. BOOTSELボタンを押してスタート
5. もう一度BOOTSELボタンを押すと停止

重み付けアルゴリズム:
- 各センサーに重み [-7, -5, -3, -1, 1, 3, 5, 7] を割り当て
- 黒（ライン）を検出したセンサーの重みを平均してライン位置を算出
- PD制御で左右モーターの速度を調整
"""

from machine import Pin, PWM
from utime import sleep
import time
try:
    import rp2
except ImportError:
    rp2 = None

# ===== ピン設定 =====
# モーター（MakerDrive）
M1A = PWM(Pin(5))  # 左モーター前進
M1B = PWM(Pin(4))  # 左モーター後退
M2A = PWM(Pin(3))  # 右モーター前進
M2B = PWM(Pin(2))  # 右モーター後退

# 8個のフォトリフレクタ（左から右へ）
SENSOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]
sensors = [Pin(pin, Pin.IN) for pin in SENSOR_PINS]

# PWM周波数設定
M1A.freq(1000)
M1B.freq(1000)
M2A.freq(1000)
M2B.freq(1000)

# ===== 制御パラメータ =====
SENSOR_WEIGHTS = [-7, -5, -3, -1, 1, 3, 5, 7]  # センサーの重み
BASE_SPEED = 30000  # 基本速度
MAX_SPEED = 54613   # 最大速度
KP = 50  # 比例ゲイン
KD = 10  # 微分ゲイン

# 制御変数
last_error = 0
last_position = 0


def read_sensors():
    """全センサーの値を読む"""
    return [sensor.value() for sensor in sensors]


def calculate_line_position():
    """重み付け平均でライン位置を計算"""
    global last_position

    values = read_sensors()
    weighted_sum = 0
    sensor_count = 0

    # 黒（0）を検出したセンサーのみで重み付け平均
    for i, value in enumerate(values):
        if value == 0:
            weighted_sum += SENSOR_WEIGHTS[i]
            sensor_count += 1

    if sensor_count > 0:
        position = weighted_sum / sensor_count
        last_position = position
        return position, True
    else:
        return last_position, False


def pd_control(line_position, on_line):
    """PD制御でモーター速度を計算"""
    global last_error

    if not on_line:
        # ラインロスト: 前回の誤差で探索
        if last_error < 0:
            # 左に探索
            return 0, BASE_SPEED
        else:
            # 右に探索
            return BASE_SPEED, 0

    # PD制御計算
    error = line_position
    derivative = error - last_error
    correction = int(KP * error + KD * derivative)
    last_error = error

    # モーター速度計算
    left_speed = BASE_SPEED - correction
    right_speed = BASE_SPEED + correction

    # 速度制限
    left_speed = max(0, min(MAX_SPEED, left_speed))
    right_speed = max(0, min(MAX_SPEED, right_speed))

    return left_speed, right_speed


def set_motor_speed(left, right):
    """モーター速度設定"""
    M1A.duty_u16(left)
    M1B.duty_u16(0)
    M2A.duty_u16(right)
    M2B.duty_u16(0)


def stop_motors():
    """モーター停止"""
    M1A.duty_u16(0)
    M1B.duty_u16(0)
    M2A.duty_u16(0)
    M2B.duty_u16(0)


def get_debug_info():
    """デバッグ情報取得"""
    values = read_sensors()
    position, on_line = calculate_line_position()
    visual = ''.join(['■' if v == 0 else '□' for v in values])
    status = "ON" if on_line else "LOST"
    return f"{visual} | Pos: {position:+.2f} | {status}"


# ===== メインプログラム =====
print("=" * 60)
print("ライントレースカー - 8センサー重み付け制御")
print("=" * 60)
print("\n設定:")
print(f"- センサー: {len(SENSOR_PINS)}個 (GPIO {SENSOR_PINS})")
print(f"- 重み: {SENSOR_WEIGHTS}")
print(f"- 基本速度: {BASE_SPEED}, 最大速度: {MAX_SPEED}")
print(f"- PID: Kp={KP}, Kd={KD}")
print()

# BOOTSELボタンでスタート待機
if rp2:
    print("BOOTSELボタンを押してスタート...")
    while rp2.bootsel_button() == 0:
        time.sleep(0.1)
    time.sleep(0.5)
    print("スタート!\n")
else:
    print("3秒後にスタート...")
    time.sleep(3)
    print("スタート!\n")

time_start = time.time()
loop_count = 0

try:
    while True:
        # BOOTSELボタンで停止
        if rp2 and rp2.bootsel_button() == 1:
            print("\nBOOTSELボタンで停止しました")
            break

        # ライン位置計算
        line_position, on_line = calculate_line_position()

        # PD制御でモーター速度計算
        left_speed, right_speed = pd_control(line_position, on_line)

        # モーター駆動
        set_motor_speed(left_speed, right_speed)

        # デバッグ情報表示（10ループごと）
        loop_count += 1
        if loop_count % 10 == 0:
            print(get_debug_info())

        sleep(0.01)

except KeyboardInterrupt:
    print("\nCtrl+Cで停止しました")
finally:
    stop_motors()
    elapsed = time.time() - time_start
    print(f"\n走行時間: {elapsed:.1f}秒")
    print(f"ループ回数: {loop_count}")
    print("プログラム終了")

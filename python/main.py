import RPi.GPIO as GPIO
import time

# GPIOピン定義
# ラインセンサー (デジタル入力)
SENSOR_LEFT_PIN = 17    # GPIO 17
SENSOR_CENTER_PIN = 27  # GPIO 27
SENSOR_RIGHT_PIN = 22   # GPIO 22

# モーター制御ピン (PWM出力と方向制御)
# 左モーター
MOTOR_LEFT_PWM_PIN = 18   # GPIO 18 (PWM)
MOTOR_LEFT_DIR_PIN = 23   # GPIO 23 (方向: HIGH/LOW)
# 右モーター
MOTOR_RIGHT_PWM_PIN = 24  # GPIO 24 (PWM)
MOTOR_RIGHT_DIR_PIN = 25  # GPIO 25 (方向: HIGH/LOW)

# 速度設定
BASE_SPEED = 60   # 基本的な直進速度 (0-100のデューティ比)
TURN_ADJUST = 30  # 旋回時の速度調整量

# GPIO設定
GPIO.setmode(GPIO.BCM) # BCMモード (GPIO番号で指定)
GPIO.setup(SENSOR_LEFT_PIN, GPIO.IN)
GPIO.setup(SENSOR_CENTER_PIN, GPIO.IN)
GPIO.setup(SENSOR_RIGHT_PIN, GPIO.IN)

GPIO.setup(MOTOR_LEFT_PWM_PIN, GPIO.OUT)
GPIO.setup(MOTOR_LEFT_DIR_PIN, GPIO.OUT)
GPIO.setup(MOTOR_RIGHT_PWM_PIN, GPIO.OUT)
GPIO.setup(MOTOR_RIGHT_DIR_PIN, GPIO.OUT)

# PWMオブジェクトの作成 (周波数50Hz)
pwm_left = GPIO.PWM(MOTOR_LEFT_PWM_PIN, 50)
pwm_right = GPIO.PWM(MOTOR_RIGHT_PWM_PIN, 50)

# PWM開始 (最初は停止)
pwm_left.start(0)
pwm_right.start(0)

# モーターの方向を常に前進に設定
GPIO.output(MOTOR_LEFT_DIR_PIN, GPIO.HIGH)
GPIO.output(MOTOR_RIGHT_DIR_PIN, GPIO.HIGH)

def set_motors(left_speed, right_speed):
    """
    モーターの速度を設定する関数 (デューティ比 0-100)
    """
    # 速度が0-100の範囲に収まるように調整
    left_speed = max(0, min(100, left_speed))
    right_speed = max(0, min(100, right_speed))

    pwm_left.ChangeDutyCycle(left_speed)
    pwm_right.ChangeDutyCycle(right_speed)

try:
    while True:
        # センサー値の読み取り
        # デジタルセンサーの場合、HIGH/LOWでラインの有無を判断
        # 例: HIGHでラインを検知、LOWでラインなし
        left_on_line = GPIO.input(SENSOR_LEFT_PIN) == GPIO.HIGH
        center_on_line = GPIO.input(SENSOR_CENTER_PIN) == GPIO.HIGH
        right_on_line = GPIO.input(SENSOR_RIGHT_PIN) == GPIO.HIGH

        # デバッグ出力
        print(f"L:{left_on_line} C:{center_on_line} R:{right_on_line}")

        # 制御ロジック
        if center_on_line:
            # 中央センサーがライン上: 直進
            set_motors(BASE_SPEED, BASE_SPEED)
        elif left_on_line:
            # 左センサーがライン上: 右に旋回 (右モーターを速く)
            set_motors(BASE_SPEED - TURN_ADJUST, BASE_SPEED + TURN_ADJUST)
        elif right_on_line:
            # 右センサーがライン上: 左に旋回 (左モーターを速く)
            set_motors(BASE_SPEED + TURN_ADJUST, BASE_SPEED - TURN_ADJUST)
        else:
            # ラインを見失った場合: 一旦停止
            set_motors(0, 0)
        
        # 短い遅延 (CPU使用率を抑えるため)
        time.sleep(0.01)

except KeyboardInterrupt:
    # Ctrl+Cで終了した場合のクリーンアップ
    print("プログラムを終了します。")
    pwm_left.stop()
    pwm_right.stop()
    GPIO.cleanup()

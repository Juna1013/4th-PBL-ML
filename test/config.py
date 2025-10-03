"""
テスト用設定ファイル
必要に応じてパラメータを調整
"""

# モーターピン（MakerDrive）
MOTOR_LEFT_FWD = 5   # M1A
MOTOR_LEFT_REV = 4   # M1B
MOTOR_RIGHT_FWD = 3  # M2A
MOTOR_RIGHT_REV = 2  # M2B

# フォトリフレクタピン（左から右へ8個）
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]

# センサー重み（左から右へ）
SENSOR_WEIGHTS = [-7, -5, -3, -1, 1, 3, 5, 7]

# 速度設定
BASE_SPEED = 30000  # 基本速度（0-65535）
MAX_SPEED = 54613   # 最大速度

# PID制御パラメータ
KP = 50  # 比例ゲイン（大きいほど反応が速い）
KI = 0   # 積分ゲイン（未使用）
KD = 10  # 微分ゲイン（大きいほど滑らか）

# デバッグ設定
DEBUG_INTERVAL = 20  # デバッグ表示の間隔（ループ回数）

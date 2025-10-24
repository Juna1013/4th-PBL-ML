# Pico W Configuration
# WiFi-�
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# ����-�
SERVER_URL = "https://your-api-server.render.com/api"  # RendernURL
# ~_o�zB: "http://192.168.1.100:8000/api"

# ピン設定
AUDIO_PIN = 26  # 音声センサー（ADC0）
MOTOR_LEFT_PIN = 5  # M1A
MOTOR_RIGHT_PIN = 3  # M2A
MOTOR_LEFT_DIR_PIN = 4  # M1B
MOTOR_RIGHT_DIR_PIN = 2  # M2B

# センサーピン設定（ライントレース用 - 8個のフォトリフレクタ）
# 左から右へ順番に配置: 0-7
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]  # GPIO 16-22, 28

# タイミング設定
COMMAND_CHECK_INTERVAL = 1.0  # 秒
AUDIO_RECORD_DURATION = 1000  # ミリ秒

# ライントレース設定
LINE_TRACE_SPEED_PERCENT = 83  # ライントレース時の速度（100/1.2 ≈ 83%）
BASE_LINE_SPEED = 30000  # 基本速度（PWM duty）
MAX_LINE_SPEED = 54613  # 最大速度（duty_100 / 1.2）

# 重み付け設定（8個センサー用）
SENSOR_WEIGHTS = [-7, -5, -3, -1, 1, 3, 5, 7]  # 左から右へ：負の値は左、正の値は右
# センサー位置: [0=最左, 1, 2, 3, 4, 5, 6, 7=最右]

# PID制御パラメータ
KP = 50  # 比例ゲイン
KI = 0   # 積分ゲイン（将来的に使用可能）
KD = 10  # 微分ゲイン

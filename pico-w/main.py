"""
Pico W ライントレースカー制御システム
音声認識 + WiFi制御 + ライントレース機能
全てのモジュールを統合したメインプログラム
"""

import time
import gc
import machine
import array
import network
import urequests
import ujson
from machine import Pin, PWM
try:
    import rp2
except ImportError:
    rp2 = None

# ===== 設定 (config.py) =====
# WiFi設定
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# サーバー設定
SERVER_URL = "https://your-api-server.render.com/api"

# ピン設定
AUDIO_PIN = 26  # 音声センサー（ADC0）
MOTOR_LEFT_PIN = 5  # M1A
MOTOR_RIGHT_PIN = 3  # M2A
MOTOR_LEFT_DIR_PIN = 4  # M1B
MOTOR_RIGHT_DIR_PIN = 2  # M2B

# センサーピン設定（ライントレース用 - 8個のフォトリフレクタ）
PHOTOREFLECTOR_PINS = [16, 17, 18, 19, 20, 21, 22, 28]

# タイミング設定
COMMAND_CHECK_INTERVAL = 1.0  # 秒
AUDIO_RECORD_DURATION = 1000  # ミリ秒

# ライントレース設定
LINE_TRACE_SPEED_PERCENT = 83
BASE_LINE_SPEED = 30000
MAX_LINE_SPEED = 54613

# 重み付け設定（8個センサー用）
SENSOR_WEIGHTS = [-7, -5, -3, -1, 1, 3, 5, 7]

# PID制御パラメータ
KP = 50  # 比例ゲイン
KI = 0   # 積分ゲイン
KD = 10  # 微分ゲイン


# ===== AudioCapture クラス =====
class AudioCapture:
    def __init__(self, pin=26, sample_rate=16000):
        self.adc = machine.ADC(pin)
        self.sample_rate = sample_rate
    
    def record(self, duration_ms=1000):
        samples = array.array('H', [0] * (self.sample_rate * duration_ms // 1000))
        return samples


# ===== WiFiClient クラス =====
class WiFiClient:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.is_connected = False
        self.server_url = SERVER_URL

    def connect_wifi(self):
        """WiFi接続"""
        self.wlan.active(True)
        if not self.wlan.isconnected():
            print(f"WiFi接続中... SSID: {WIFI_SSID}")
            self.wlan.connect(WIFI_SSID, WIFI_PASSWORD)

            # 接続待ち
            timeout = 10
            while not self.wlan.isconnected() and timeout > 0:
                time.sleep(1)
                timeout -= 1

        if self.wlan.isconnected():
            self.is_connected = True
            print(f"WiFi接続完了: {self.wlan.ifconfig()}")
            return True
        else:
            print("WiFi接続失敗")
            return False

    def get_latest_command(self):
        """サーバーから最新コマンドを取得"""
        if not self.is_connected:
            if not self.connect_wifi():
                return "STOP"

        try:
            url = f"{self.server_url}/command/latest"
            response = urequests.get(url, timeout=5)

            if response.status_code == 200:
                data = ujson.loads(response.text)
                command = data.get("command", "STOP")
                print(f"取得したコマンド: {command}")
                return command
            else:
                print(f"サーバーエラー: {response.status_code}")
                return "STOP"

        except Exception as e:
            print(f"通信エラー: {e}")
            return "STOP"
        finally:
            if 'response' in locals():
                response.close()

    def send_audio_to_server(self, audio_data):
        """音声データをサーバーに送信（未実装）"""
        if not self.is_connected:
            if not self.connect_wifi():
                return "STOP"

        try:
            # 音声データをbase64エンコードして送信
            # 現在は未実装なので最新コマンドを取得
            return self.get_latest_command()
        except Exception as e:
            print(f"音声送信エラー: {e}")
            return "STOP"

    def send_status(self, status):
        """Pico Wのステータスをサーバーに送信"""
        if not self.is_connected:
            return False

        try:
            url = f"{self.server_url}/pico/status"
            data = {"status": status, "timestamp": time.time()}
            headers = {"Content-Type": "application/json"}

            response = urequests.post(
                url,
                data=ujson.dumps(data),
                headers=headers,
                timeout=3
            )

            success = response.status_code == 200
            response.close()
            return success

        except Exception as e:
            print(f"ステータス送信エラー: {e}")
            return False


# ===== PhotoReflector クラス =====
class PhotoReflector:
    """8個のデジタルフォトリフレクタ - 重み付けライントレース用"""

    def __init__(self):
        # 8個のセンサーを初期化
        self.sensors = [Pin(pin, Pin.IN) for pin in PHOTOREFLECTOR_PINS]
        self.num_sensors = len(self.sensors)
        self.weights = SENSOR_WEIGHTS
        self.last_position = 0  # 前回のライン位置（ラインロスト時用）
        print(f"フォトリフレクタ初期化完了: {self.num_sensors}個")

    def read_all(self):
        """
        全センサーの値を読む
        戻り値: リスト [sensor0, sensor1, ..., sensor7]
               各値: 0=ライン検出（黒）, 1=ライン外（白）
        """
        return [sensor.value() for sensor in self.sensors]

    def calculate_line_position(self):
        """
        重み付け平均でライン位置を計算

        アルゴリズム:
        1. 各センサーの値を読む（0=黒/ライン, 1=白/背景）
        2. 黒を検出したセンサーに重みを掛けて加算
        3. 検出したセンサー数で割って平均位置を算出

        戻り値:
            position: ライン位置 (-7 ~ +7)
                     負の値 = ラインは左側
                     0 = 中央
                     正の値 = ラインは右側
            on_line: ラインを検出しているか（True/False）
        """
        sensor_values = self.read_all()

        # 黒を検出したセンサー（値が0）のみを使って重み付け平均を計算
        weighted_sum = 0
        sensor_count = 0

        for i, value in enumerate(sensor_values):
            if value == 0:  # 黒（ライン）を検出
                weighted_sum += self.weights[i]
                sensor_count += 1

        # ラインを検出している場合
        if sensor_count > 0:
            position = weighted_sum / sensor_count
            self.last_position = position  # 次回のラインロスト用に保存
            return position, True
        else:
            # ラインロスト: 前回の位置を返す
            return self.last_position, False

    def get_sensor_debug_info(self):
        """デバッグ用: センサー状態を文字列で返す"""
        values = self.read_all()
        position, on_line = self.calculate_line_position()

        # センサー状態を視覚的に表示（■=黒/ライン, □=白/背景）
        visual = ''.join(['■' if v == 0 else '□' for v in values])
        status = "ON" if on_line else "LOST"

        return f"{visual} | Pos: {position:+.2f} | {status}"


# ===== MotorController クラス =====
class MotorController:
    def __init__(self):
        # モーター制御ピン設定（MakerDrive互換）
        # M1A, M1B: 左モーター, M2A, M2B: 右モーター
        self.left_motor_fwd = machine.PWM(machine.Pin(MOTOR_LEFT_PIN))  # M1A
        self.left_motor_rev = machine.PWM(machine.Pin(MOTOR_LEFT_DIR_PIN))  # M1B
        self.right_motor_fwd = machine.PWM(machine.Pin(MOTOR_RIGHT_PIN))  # M2A
        self.right_motor_rev = machine.PWM(machine.Pin(MOTOR_RIGHT_DIR_PIN))  # M2B

        # PWM周波数設定
        self.left_motor_fwd.freq(1000)
        self.left_motor_rev.freq(1000)
        self.right_motor_fwd.freq(1000)
        self.right_motor_rev.freq(1000)

        # 速度設定
        self.duty_100 = 65535  # 100% duty cycle
        self.base_speed = 32768  # 50% - コマンド制御用
        self.turn_speed = 20000   # 旋回時速度
        self.line_trace_speed = int(self.duty_100 / 1.2)  # ライントレース速度（約83%）
        self.current_command = "STOP"
        self.line_trace_mode = False

        # PID制御用変数（重み付けライントレース用）
        self.last_error = 0
        self.base_line_speed = BASE_LINE_SPEED
        self.max_line_speed = MAX_LINE_SPEED
        self.kp = KP
        self.kd = KD

    def execute_command(self, command):
        """サーバーコマンドを実行"""
        if command == self.current_command:
            return  # 同じコマンドは実行しない

        self.current_command = command
        print(f"コマンド実行: {command}")

        if command == "FORWARD":
            self.move_forward()
        elif command == "BACK":
            self.move_backward()
        elif command == "LEFT":
            self.turn_left()
        elif command == "RIGHT":
            self.turn_right()
        elif command == "STOP":
            self.stop()
        else:
            print(f"不明なコマンド: {command}")
            self.stop()

    def move_forward(self):
        """前進"""
        self.left_motor_fwd.duty_u16(self.base_speed)
        self.left_motor_rev.duty_u16(0)
        self.right_motor_fwd.duty_u16(self.base_speed)
        self.right_motor_rev.duty_u16(0)

    def move_backward(self):
        """後退"""
        self.left_motor_fwd.duty_u16(0)
        self.left_motor_rev.duty_u16(self.base_speed)
        self.right_motor_fwd.duty_u16(0)
        self.right_motor_rev.duty_u16(self.base_speed)

    def turn_left(self):
        """左旋回（その場旋回）"""
        self.left_motor_fwd.duty_u16(0)
        self.left_motor_rev.duty_u16(0)
        self.right_motor_fwd.duty_u16(self.turn_speed)
        self.right_motor_rev.duty_u16(0)

    def turn_right(self):
        """右旋回（その場旋回）"""
        self.left_motor_fwd.duty_u16(self.turn_speed)
        self.left_motor_rev.duty_u16(0)
        self.right_motor_fwd.duty_u16(0)
        self.right_motor_rev.duty_u16(0)

    def stop(self):
        """停止"""
        self.left_motor_fwd.duty_u16(0)
        self.left_motor_rev.duty_u16(0)
        self.right_motor_fwd.duty_u16(0)
        self.right_motor_rev.duty_u16(0)
        self.current_command = "STOP"

    # ===== ライントレース用メソッド =====

    def line_trace_forward(self):
        """ライントレース: 直進"""
        self.left_motor_fwd.duty_u16(self.line_trace_speed)
        self.left_motor_rev.duty_u16(0)
        self.right_motor_fwd.duty_u16(self.line_trace_speed)
        self.right_motor_rev.duty_u16(0)

    def line_trace_turn_left(self):
        """ライントレース: 左旋回（右モーターのみ駆動）"""
        self.left_motor_fwd.duty_u16(0)
        self.left_motor_rev.duty_u16(0)
        self.right_motor_fwd.duty_u16(self.line_trace_speed)
        self.right_motor_rev.duty_u16(0)

    def line_trace_turn_right(self):
        """ライントレース: 右旋回（左モーターのみ駆動）"""
        self.left_motor_fwd.duty_u16(self.line_trace_speed)
        self.left_motor_rev.duty_u16(0)
        self.right_motor_fwd.duty_u16(0)
        self.right_motor_rev.duty_u16(0)

    def line_trace_control(self, left_sensor, right_sensor):
        """
        2個センサー用の旧ライントレース制御（後方互換性用）

        Args:
            left_sensor: 左センサー値（0=ライン検出, 1=ライン外）
            right_sensor: 右センサー値（0=ライン検出, 1=ライン外）
        """
        if right_sensor == 0:
            # 右センサーがラインを検出 → 左旋回
            self.line_trace_turn_left()
        elif left_sensor == 0:
            # 左センサーがラインを検出 → 右旋回
            self.line_trace_turn_right()
        else:
            # 両センサーともラインを検出していない → 直進
            self.line_trace_forward()

    # ===== 重み付けベースのライントレース制御（8センサー用） =====

    def line_trace_weighted_control(self, line_position, on_line):
        """
        重み付け位置情報に基づくPD制御でライントレース

        Args:
            line_position: ライン位置 (-7 ~ +7)
                          負の値 = ラインは左側（右に曲がる必要）
                          0 = 中央
                          正の値 = ラインは右側（左に曲がる必要）
            on_line: ラインを検出しているか
        """
        # 目標位置は0（中央）なので、エラー = 現在位置
        error = line_position

        # PD制御: 補正値 = Kp * error + Kd * (error - last_error)
        derivative = error - self.last_error
        correction = int(self.kp * error + self.kd * derivative)

        # 次回用に保存
        self.last_error = error

        # ラインロスト時の処理
        if not on_line:
            # 前回の誤差に基づいて探索
            if self.last_error < 0:
                # ラインは左側にあった → 左に探索
                self.line_trace_turn_left()
            else:
                # ラインは右側にあった → 右に探索
                self.line_trace_turn_right()
            return

        # モーター速度を計算
        # correction > 0: ラインは右側 → 左モーター減速、右モーター加速
        # correction < 0: ラインは左側 → 右モーター減速、左モーター加速
        left_speed = self.base_line_speed - correction
        right_speed = self.base_line_speed + correction

        # 速度制限（0 ~ MAX_LINE_SPEED）
        left_speed = max(0, min(self.max_line_speed, left_speed))
        right_speed = max(0, min(self.max_line_speed, right_speed))

        # モーター駆動
        self.left_motor_fwd.duty_u16(left_speed)
        self.left_motor_rev.duty_u16(0)
        self.right_motor_fwd.duty_u16(right_speed)
        self.right_motor_rev.duty_u16(0)

    def reset_pid(self):
        """PID制御変数をリセット"""
        self.last_error = 0

    def set_speed(self, speed_percent):
        """速度設定（0-100%）"""
        if 0 <= speed_percent <= 100:
            self.base_speed = int(65535 * speed_percent / 100)
            self.turn_speed = int(self.base_speed * 0.7)  # 旋回は70%
            print(f"速度設定: {speed_percent}%")

    def emergency_stop(self):
        """緊急停止"""
        self.stop()
        print("緊急停止実行")

    def cleanup(self):
        """モーター終了処理"""
        self.stop()
        self.left_motor_fwd.deinit()
        self.left_motor_rev.deinit()
        self.right_motor_fwd.deinit()
        self.right_motor_rev.deinit()


# ===== LineTraceController クラス =====
class LineTraceController:
    """ライントレース専用コントローラー"""

    def __init__(self, motor, sensor):
        """
        Args:
            motor: MotorControllerインスタンス
            sensor: PhotoReflectorインスタンス
        """
        self.motor = motor
        self.sensor = sensor
        self.running = True
        self.bootsel_available = rp2 is not None

    def check_bootsel_button(self):
        """BOOTSELボタンチェック（緊急停止用）"""
        if self.bootsel_available and rp2.bootsel_button() == 1:
            print("BOOTSELボタンが押されました - 緊急停止")
            self.motor.emergency_stop()
            self.running = False
            return True
        return False

    def wait_for_start(self):
        """BOOTSELボタンでスタート待機"""
        if self.bootsel_available:
            print("\n準備完了 - BOOTSELボタンを押してスタート...")
            while rp2.bootsel_button() == 0:
                time.sleep(0.1)
            time.sleep(0.5)  # チャタリング防止
            print("スタート!\n")
        else:
            print("3秒後にスタート...")
            time.sleep(3)
            print("スタート!\n")

    def run(self):
        """ライントレースモードを実行"""
        print("=" * 50)
        print("ライントレースモード開始（8センサー重み付け制御）")
        print("=" * 50)
        print("BOOTSELボタンで停止できます" if self.bootsel_available else "Ctrl+Cで停止してください")

        # PID制御をリセット
        self.motor.reset_pid()

        # スタート待機
        self.wait_for_start()

        loop_count = 0

        try:
            while self.running:
                # BOOTSELボタンチェック
                if self.check_bootsel_button():
                    break

                # 8個のフォトリフレクタから重み付け位置を計算
                line_position, on_line = self.sensor.calculate_line_position()

                # 重み付けベースのPD制御でライントレース
                self.motor.line_trace_weighted_control(line_position, on_line)

                # デバッグ情報を定期的に表示（10ループごと）
                loop_count += 1
                if loop_count % 10 == 0:
                    debug_info = self.sensor.get_sensor_debug_info()
                    print(debug_info)

                # センサー読み取り間隔
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\nCtrl+Cで停止しました")
        finally:
            self.motor.stop()
            print("\nライントレースモード終了")


# ===== PicoWController クラス (メインコントローラー) =====
class PicoWController:
    """メインコントローラー"""

    def __init__(self):
        print("Pico W ライントレースカー制御システム起動中...")

        # 各モジュールの初期化
        self.audio = AudioCapture()
        self.motor = MotorController()
        self.wifi = WiFiClient()
        self.sensor = PhotoReflector()

        # ライントレースコントローラー
        self.line_tracer = LineTraceController(self.motor, self.sensor)

        self.running = True
        self.last_command = "STOP"

    def initialize(self):
        """システム初期化"""
        print("WiFi接続を開始...")
        if not self.wifi.connect_wifi():
            print("WiFi接続に失敗しました。オフラインモードで動作します。")
            return False

        # 初期状態をサーバーに送信
        self.wifi.send_status("初期化完了")
        print("システム初期化完了")
        return True

    def handle_command(self, command):
        """コマンド処理"""
        if command == "LINE_TRACE":
            # ライントレースモードに切り替え
            self.line_tracer.run()
            return "STOP"  # ライントレース終了後は停止状態に
        else:
            # 通常のモーターコマンド
            self.motor.execute_command(command)
            return command

    def main_loop(self):
        """メインループ"""
        while self.running:
            try:
                # サーバーから最新コマンドを取得
                command = self.wifi.get_latest_command()

                # コマンドが変更された場合のみ実行
                if command != self.last_command:
                    print(f"新しいコマンド: {self.last_command} → {command}")

                    # コマンド処理
                    self.last_command = self.handle_command(command)

                    # ステータスをサーバーに送信
                    self.wifi.send_status(f"コマンド実行: {command}")

                # 指定された間隔で待機
                time.sleep(COMMAND_CHECK_INTERVAL)

                # メモリクリーンアップ
                if hasattr(gc, 'collect'):
                    gc.collect()

            except KeyboardInterrupt:
                print("停止コマンドを受信しました")
                break
            except Exception as e:
                print(f"エラーが発生しました: {e}")
                self.motor.stop()
                time.sleep(1)

    def shutdown(self):
        """システム終了処理"""
        print("システムを終了しています...")
        self.running = False
        self.motor.emergency_stop()
        self.wifi.send_status("システム終了")
        self.motor.cleanup()
        print("システム終了完了")


# ===== スタンドアロンライントレース機能 =====
def run_standalone_line_trace():
    """
    スタンドアロンライントレースプログラム（WiFi接続不要）
    
    使い方:
    1. GPIO 16-22, 28に8個のフォトリフレクタを接続（左から右へ順番）
    2. GPIO 2-5にモーター（MakerDrive）を接続
    3. BOOTSELボタンを押してスタート
    4. もう一度BOOTSELボタンを押すと停止
    """
    print("=" * 60)
    print("ライントレースカー - 8センサー重み付け制御（スタンドアロン）")
    print("=" * 60)
    print("\n設定:")
    print(f"- センサー: {len(PHOTOREFLECTOR_PINS)}個 (GPIO {PHOTOREFLECTOR_PINS})")
    print(f"- 重み: {SENSOR_WEIGHTS}")
    print(f"- 基本速度: {BASE_LINE_SPEED}, 最大速度: {MAX_LINE_SPEED}")
    print(f"- PID: Kp={KP}, Kd={KD}")
    print()

    # モーターとセンサーを初期化
    motor = MotorController()
    sensor = PhotoReflector()
    line_tracer = LineTraceController(motor, sensor)

    try:
        # ライントレース実行
        line_tracer.run()
    finally:
        motor.cleanup()
        print("スタンドアロンライントレース終了")


# ===== メイン実行部分 =====
if __name__ == "__main__":
    import sys
    
    # コマンドライン引数で動作モードを選択
    if len(sys.argv) > 1 and sys.argv[1] == "standalone":
        # スタンドアロンライントレースモード（WiFi不要）
        run_standalone_line_trace()
    else:
        # 通常モード（WiFi + サーバー制御）
        controller = PicoWController()

        try:
            # システム初期化
            if controller.initialize():
                print("制御ループを開始します...")
                controller.main_loop()
            else:
                print("初期化に失敗しました")

        except Exception as e:
            print(f"システムエラー: {e}")
        finally:
            controller.shutdown()

"""
ライントレース制御モジュール
BOOTSELボタン、センサー、モーターを統合した制御
"""

import time
try:
    import rp2
except ImportError:
    rp2 = None


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

import time
import asyncio
import gc
from audio_capture import AudioCapture
from motor_control import MotorController
from wifi_client import WiFiClient
from config import COMMAND_CHECK_INTERVAL

class PicoWController:
    def __init__(self):
        print("Pico W ライントレースカー制御システム起動中...")
        self.audio = AudioCapture()
        self.motor = MotorController()
        self.wifi = WiFiClient()
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

    def main_loop(self):
        """メインループ"""
        while self.running:
            try:
                # サーバーから最新コマンドを取得
                command = self.wifi.get_latest_command()

                # コマンドが変更された場合のみ実行
                if command != self.last_command:
                    print(f"新しいコマンド: {self.last_command} → {command}")
                    self.motor.execute_command(command)
                    self.last_command = command

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

# メイン実行部分
if __name__ == "__main__":
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

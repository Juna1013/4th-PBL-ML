'''
テレメトリ送信モジュール
センサーとモーターの状態をサーバーに送信
'''

import urequests
import ujson
import time
import gc

class TelemetryClient:
    """テレメトリデータを送信するクライアント"""
    
    def __init__(self, server_url, timeout=5):
        """
        Args:
            server_url: テレメトリサーバーのURL
            timeout: リクエストタイムアウト（秒）
        """
        self.server_url = server_url
        self.timeout = timeout
        self.success_count = 0
        self.fail_count = 0
    
    def send(self, sensor_values, motor_left, motor_right, error, turn, base_speed, network_manager):
        """
        テレメトリデータを送信
        
        Args:
            sensor_values: センサー値のリスト
            motor_left: 左モーター速度
            motor_right: 右モーター速度
            error: 制御誤差
            turn: 旋回量
            base_speed: 基本速度
            network_manager: NetworkManagerインスタンス
        
        Returns:
            bool: 送信成功時True
        """
        try:
            data = {
                "timestamp": time.ticks_ms(),
                "sensors": sensor_values,
                "motor": {
                    "left_speed": motor_left,
                    "right_speed": motor_right
                },
                "control": {
                    "error": error,
                    "turn": turn,
                    "base_speed": base_speed
                },
                "wifi": {
                    "ip": network_manager.get_ip(),
                    "rssi": network_manager.get_rssi()
                }
            }
            
            json_data = ujson.dumps(data)
            headers = {'Content-Type': 'application/json'}
            
            response = urequests.post(
                self.server_url,
                data=json_data,
                headers=headers,
                timeout=self.timeout
            )
            
            status = response.status_code
            response.close()
            gc.collect()  # メモリ解放
            
            if status == 200:
                self.success_count += 1
                return True
            else:
                self.fail_count += 1
                return False
            
        except Exception as e:
            self.fail_count += 1
            print(f"❌ テレメトリ送信エラー: {e}")
            return False
    
    def get_stats(self):
        """送信統計を取得"""
        return {
            "success": self.success_count,
            "fail": self.fail_count,
            "total": self.success_count + self.fail_count
        }
    
    def reset_stats(self):
        """統計をリセット"""
        self.success_count = 0
        self.fail_count = 0

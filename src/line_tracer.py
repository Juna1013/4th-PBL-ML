'''
ライントレース制御モジュール
センサー読み取り、モーター制御、PD制御を実装
'''

from machine import Pin, PWM
import time

class LineTracer:
    """ライントレース制御を行うクラス"""
    
    def __init__(self, config):
        """
        Args:
            config: 設定辞書
                - sensor_pins: センサーピンのリスト
                - left_fwd_pin, left_rev_pin: 左モーターピン
                - right_fwd_pin, right_rev_pin: 右モーターピン
                - base_speed: 基本速度
                - left_correction: 左モーター補正値
                - right_correction: 右モーター補正値
                - kp, kd: PD制御ゲイン
                - weights: センサー重み
        """
        # 設定を保存
        self.base_speed = config['base_speed']
        self.left_correction = config['left_correction']
        self.right_correction = config['right_correction']
        self.kp = config['kp']
        self.kd = config['kd']
        self.weights = config['weights']
        
        # センサー初期化
        self.sensors = [Pin(p, Pin.IN, Pin.PULL_UP) for p in config['sensor_pins']]
        
        # モーター初期化
        self.left_fwd = PWM(Pin(config['left_fwd_pin']))
        self.left_rev = PWM(Pin(config['left_rev_pin']))
        self.right_fwd = PWM(Pin(config['right_fwd_pin']))
        self.right_rev = PWM(Pin(config['right_rev_pin']))
        
        for pwm in [self.left_fwd, self.left_rev, self.right_fwd, self.right_rev]:
            pwm.freq(1000)
        
        # 状態変数
        self.current_left_speed = 0
        self.current_right_speed = 0
        self.current_sensor_values = [0] * len(self.sensors)
        self.current_error = 0
        self.current_turn = 0
        self.last_error = 0
        
        print("✅ ライントレーサー初期化完了")
    
    def read_sensors(self):
        """センサー値を読み取る"""
        self.current_sensor_values = [s.value() for s in self.sensors]
        return self.current_sensor_values
    
    def calculate_error(self, values):
        """センサー値から誤差を計算"""
        detected_count = 0
        weighted_sum = 0.0
        
        for i in range(len(values)):
            if values[i] == 0:  # 黒ライン検出
                weighted_sum += self.weights[i]
                detected_count += 1
        
        if detected_count == 0:
            return None  # ライン未検出
        else:
            return -(weighted_sum / detected_count)
    
    def set_motors(self, left_duty, right_duty):
        """モーター速度を設定"""
        # モーター補正適用
        left_duty = int(left_duty * self.left_correction)
        right_duty = int(right_duty * self.right_correction)
        
        # PWM範囲に制限
        left_duty = max(0, min(65535, left_duty))
        right_duty = max(0, min(65535, right_duty))
        
        # 状態を保存
        self.current_left_speed = left_duty
        self.current_right_speed = right_duty
        
        # モーター駆動
        self.left_fwd.duty_u16(left_duty)
        self.left_rev.duty_u16(0)
        self.right_fwd.duty_u16(0)
        self.right_rev.duty_u16(right_duty)
    
    def stop(self):
        """モーターを停止"""
        for pwm in [self.left_fwd, self.left_rev, self.right_fwd, self.right_rev]:
            pwm.duty_u16(0)
        self.current_left_speed = 0
        self.current_right_speed = 0
        print("🛑 モーター停止")
    
    def step(self):
        """
        1ステップのライントレース処理
        
        Returns:
            bool: ライン検出成功時True
        """
        # センサー読み取り
        values = self.read_sensors()
        
        # 誤差計算
        error = self.calculate_error(values)
        if error is None:
            error = self.last_error  # ライン未検出時は前回の誤差を使用
            line_detected = False
        else:
            line_detected = True
        
        self.current_error = error
        
        # PD制御
        error_diff = error - self.last_error
        turn = int(self.kp * error + self.kd * error_diff)
        self.current_turn = turn
        self.last_error = error
        
        # ターン量を制限
        turn = max(-self.base_speed, min(self.base_speed, turn))
        
        # 誤差に応じて減速（急カーブで強く減速）
        speed_factor = max(0.3, 1.0 - abs(error)/10)
        left_speed = int((self.base_speed - turn) * speed_factor)
        right_speed = int((self.base_speed + turn) * speed_factor)
        
        self.set_motors(left_speed, right_speed)
        
        return line_detected
    
    def get_state(self):
        """現在の状態を取得"""
        return {
            "sensors": self.current_sensor_values,
            "motor_left": self.current_left_speed,
            "motor_right": self.current_right_speed,
            "error": self.current_error,
            "turn": self.current_turn,
            "base_speed": self.base_speed
        }

from machine import Pin
from config import PHOTOREFLECTOR_PINS, SENSOR_WEIGHTS

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
                     負の値 = ライン��左側
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

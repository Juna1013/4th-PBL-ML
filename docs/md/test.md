# ライントレースプログラム解説

`firmware/test/integration_test/test.py` は、MicroPythonを使用した**ライントレースロボットの制御プログラム**です。

8個のフォトリフレクタ（センサー）でライン（黒線）を検知し、左右のモーターの速度を調整してライン上を走行するように設計されています。

## 1. ピン定義と設定

コードの冒頭部分（6-25行目）では、ハードウェアのピン配置や走行に関するパラメータを定義しています。

### ピン定義
*   `LEFT_FWD_PIN` (5), `LEFT_REV_PIN` (4): 左モーター制御ピン
*   `RIGHT_FWD_PIN` (2), `RIGHT_REV_PIN` (3): 右モーター制御ピン
*   `PHOTOREFLECTOR_PINS`: 8つのセンサーのGPIOピン番号リスト [16, 17, 18, 19, 20, 21, 22, 28]
*   `LED_PIN`: 状態表示用LED ("LED")

### 走行パラメータ
*   `WHEEL_DIAMETER`: タイヤの直径 (3.0cm)
*   `MOTOR_MAX_RPM`: モーターの最大回転数 (10000 RPM)
*   `TARGET_SPEED`: 目標速度 (5.0cm/s)
*   `MIN_PWM`: モーターが確実に回る最低PWM値 (25000)

### BASE_SPEED自動計算
目標速度から必要なモーターの回転数を逆算し、PWMのデューティ比（0〜65535）の基準値 `BASE_SPEED` を以下の式で自動計算：

```python
circumference = π × WHEEL_DIAMETER
target_rpm = (TARGET_SPEED / circumference) × 60
BASE_SPEED = max((target_rpm / MOTOR_MAX_RPM × 65535) // 4, MIN_PWM)
```

## 2. 初期化処理

27-40行目で、各デバイスの初期化を行っています。

*   **モーター**: `machine.PWM` を使用して1kHzの周波数でPWM制御を設定。4つのピン全てをループで初期化。
*   **センサー**: 8つのピンを全て入力モード (`Pin.IN`) に設定。リスト内包表記でコンパクトに記述。
*   **LED**: 出力モードに設定し、初期状態で点灯。

## 3. モーター制御関数

モーターを動かすためのヘルパー関数が定義されています（42-58行目）。

### `set_motors(left_duty, right_duty)`
*   左右のモーターのPWMデューティ比を設定します。
*   値は `MIN_PWM` 〜 `65535` の範囲に自動制限（クリップ）されます。
*   **配線の特性に対応**: 
    *   左モーター: `left_fwd` (FWDピン) にPWMを出力して前進
    *   右モーター: `right_rev` (REVピン) にPWMを出力して前進（配線が逆接続されているため）

### `stop_motors()`
*   全てのモーター出力を0にして停止させます。
*   停止メッセージを表示します。

## 4. ライントレース制御パラメータ

### 制御定数
*   `KP = 8000`: 比例ゲイン（P制御）
*   `WEIGHTS = [-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5]`: センサー位置の重み付け

## 5. ライントレース制御ループ

メインループ（67-102行目）では、以下の処理を10msごとに繰り返して自律走行を行います。

### 1. センサー読み取り
```python
values = [s.value() for s in sensors]
```
*   `sensor_test.py` で動作確認済みのシンプルな読み取り方法を採用
*   各センサーから値を読み取ります（白=1, 黒=0）

### 2. デバッグ表示（0.5秒に1回）
*   センサーの状態を `0 1 1 0 0 0 0 0` のように表示
*   LEDを点滅させて動作中であることを通知

### 3. 誤差（Error）の計算
黒線（0）を検知したセンサーだけで重み付き平均を計算：

```python
detected_count = 0
weighted_sum = 0.0
for i in range(8):
    if values[i] == 0:  # 黒を検知
        weighted_sum += WEIGHTS[i]
        detected_count += 1

if detected_count == 0:
    error = last_error  # 前回の誤差を保持
else:
    error = -(weighted_sum / detected_count)
    last_error = error
```

*   `error` はライン中心からのズレを表します
*   負の値なら左寄り、正の値なら右寄り
*   ラインが見つからない場合は、前回の誤差を保持してコースアウトを防ぎます

### 4. P制御（比例制御）
```python
turn = int(KP * error)
left_speed = BASE_SPEED - turn
right_speed = BASE_SPEED + turn
```

*   誤差に応じて左右のモーター速度に差をつけることで、ロボットの向きを修正
*   誤差が正（右寄り）: 左モーター減速、右モーター加速 → 右旋回
*   誤差が負（左寄り）: 右モーター減速、左モーター加速 → 左旋回

### 5. モーター駆動
```python
set_motors(left_speed, right_speed)
time.sleep_ms(10)
```

## 6. 安全停止機能

`try...except KeyboardInterrupt...finally` 構文を使用しており、Ctrl+Cなどでプログラムを強制終了した際に、必ず `stop_motors()` が実行され、モーターが安全に停止するよう設計されています。

## 7. トラブルシューティング

### センサーが正しく反応しない
*   `test/unit_test/sensor_test.py` を実行して、各センサーが黒=0、白=1を正しく出力しているか確認
*   センサーの高さや角度を調整

### 左右のモーター速度が異なる
*   ハードウェアの個体差により、同じPWM値でも回転数が異なることがあります
*   `set_motors()` 関数内で補正係数を追加することで調整可能

### 蛇行が激しい
*   `KP` の値を小さくする（例: 6000）
*   `BASE_SPEED` を下げる

### カーブで曲がれない
*   `KP` の値を大きくする（例: 10000）
*   `BASE_SPEED` を下げて反応時間を確保

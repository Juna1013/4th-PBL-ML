# ユーザーガイド

## セットアップと実行

### 1. 準備

1. `pico-w/` 以下のプログラムを Pico W に転送します。
2. `main.py` (または `config.py`) を開き、以下の設定を環境に合わせて編集します。
   ```python
   WIFI_SSID = "Your_SSID"
   WIFI_PASSWORD = "Your_Password"
   SERVER_URL = "http://your-server.com/api"
   ```

### 2. 実行モード

**通常モード (WiFi制御)**
```bash
python main.py
```
WiFiに接続し、サーバーからのコマンド待機状態になります。

**スタンドアロンモード (ライントレースのみ)**
```bash
python main.py standalone
```
WiFi接続を行わず、起動直後からライントレースを開始します。

## 設定とチューニング

`test/integration_test/test.py` 内の定数を変更することで、走行特性を調整できます。

### 速度設定
- `TARGET_SPEED`: 目標速度 (cm/s)。デフォルト: 5.0
- `MIN_PWM`: モーターが確実に回る最低PWM値。デフォルト: 25000
- `BASE_SPEED`: 自動計算される基本速度（0-65535）
  ```python
  circumference = π × WHEEL_DIAMETER
  target_rpm = (TARGET_SPEED / circumference) × 60
  BASE_SPEED = max((target_rpm / MOTOR_MAX_RPM × 65535) // 4, MIN_PWM)
  ```

### P制御パラメータ
ライントレースの安定性を調整します。

- **`KP` (比例ゲイン)**: デフォルト 8000
  - 値を大きくするとカーブへの反応が良くなりますが、直進でふらつきやすくなります。
  - 推奨範囲: 6000〜10000

### モーター速度補正
左右のモーターの個体差により回転数が異なる場合、`set_motors()` 関数内で補正係数を適用できます：

```python
def set_motors(left_duty, right_duty):
    # 補正係数を適用（例: 右モーターが速い場合）
    LEFT_CORRECTION = 1.0
    RIGHT_CORRECTION = 0.9  # 右を10%減速
    
    left_duty = int(left_duty * LEFT_CORRECTION)
    right_duty = int(right_duty * RIGHT_CORRECTION)
    
    # 以下、既存のコード
    ...
```

## 開発とテスト

### ユニットテスト
`test/unit_test/` 内のスクリプトを使用して、各パーツの動作確認が可能です。
- `motor_test.py`: モーター回転テスト
- `sensor_test.py`: センサー反応テスト（黒=0、白=1の確認）
- `wifi_test.py`: ネットワーク接続テスト

### 統合テスト
- `test/integration_test/test.py`: ライントレースの統合テスト
  - センサー読み取りからモーター制御まで一連の動作を確認
  - 0.5秒ごとにセンサー状態を表示

### トラブルシューティング

| 現象 | 原因と対策 |
| --- | --- |
| **WiFiに繋がらない** | SSID/Passを確認してください。Pico Wは2.4GHz帯のみ対応です。 |
| **その場で回転してしまう** | 片方のモーター配線が逆の可能性があります。ピン設定を見直してください。 |
| **左右のモーター速度が異なる** | ハードウェアの個体差です。`set_motors()`関数内で補正係数を追加してください。 |
| **ラインを無視して直進する** | センサーの高さが不適切か、黒線を認識できていません。`sensor_test.py`で各センサーが黒=0を出力するか確認してください。 |
| **激しく蛇行する** | `KP`が高すぎます。6000程度に下げてみてください。また`BASE_SPEED`を下げることも有効です。 |
| **カーブで曲がれない** | `KP`が低すぎます。10000程度に上げてみてください。または`BASE_SPEED`を下げて反応時間を確保してください。 |
| **センサーが反応しない** | `sensor_test.py`を実行して個別に確認してください。センサーの高さ・角度を調整してください。 |

## 今後の展望 (Roadmap)

- [ ] **音声コマンドの高度化**: 自然言語処理との連携
- [ ] **Web設定画面**: ブラウザから直接PIDパラメータを調整可能に
- [ ] **コース学習機能**: 走行ログに基づく最適化

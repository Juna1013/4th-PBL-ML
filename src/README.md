# Firmware Source Code

Raspberry Pi Pico W用のライントレース + テレメトリ送信プログラム

## 📁 ファイル構成

```
src/
├── main.py              # メインプログラム
├── config.py            # WiFi・サーバー設定
├── network_manager.py   # ネットワーク管理
├── telemetry.py         # テレメトリ送信
└── line_tracer.py       # ライントレース制御
```

---

## 📄 各ファイルの説明

### `main.py` (4.6KB)
**メインプログラム - 全体の制御フロー**

- 各モジュールを統合して動作
- 初期化、メインループ、クリーンアップを管理
- テレメトリ送信のタイミング制御

**主な処理:**
1. ハードウェア初期化（LED）
2. ネットワーク接続
3. ライントレーサー初期化
4. テレメトリクライアント初期化
5. メインループ（ライントレース + 定期的なテレメトリ送信）
6. 統計情報の表示

**使用方法:**
```bash
# Raspberry Pi Pico Wで実行
python main.py
```

---

### `config.py` (268B)
**設定ファイル - WiFi・サーバー情報**

```python
SSID = "iPhone SG"           # WiFi SSID
PASSWORD = "12345kurisu"     # WiFiパスワード
SERVER_IP = "172.20.10.3"    # テレメトリサーバーのIPアドレス
```

⚠️ **セキュリティ注意:**
- パスワードが含まれているため、Gitにコミットしないこと
- `.gitignore`に追加推奨

---

### `network_manager.py` (2.4KB)
**ネットワーク管理モジュール**

**クラス:** `NetworkManager`

**主な機能:**
- `connect()` - WiFi接続（30秒タイムアウト付き）
- `disconnect()` - WiFi切断
- `get_ip()` - IPアドレス取得
- `get_rssi()` - 信号強度取得
- `is_connected()` - 接続状態確認

**使用例:**
```python
network_mgr = NetworkManager(
    ssid="WiFi名",
    password="パスワード",
    led_pin="LED"
)
if network_mgr.connect():
    print(f"接続成功: {network_mgr.get_ip()}")
```

**特徴:**
- タイムアウト機能で無限ループを防止
- LED点滅で接続状態を視覚的に表示
- 接続失敗時の適切なエラーハンドリング

---

### `telemetry.py` (2.9KB)
**テレメトリ送信モジュール**

**クラス:** `TelemetryClient`

**主な機能:**
- `send()` - センサー・モーター・制御データを送信
- `get_stats()` - 送信統計取得（成功/失敗/合計）
- `reset_stats()` - 統計リセット

**送信データ形式:**
```json
{
  "timestamp": 12345,
  "sensors": [1, 1, 0, 0, 0, 1, 1, 1],
  "motor": {
    "left_speed": 6160,
    "right_speed": 8000
  },
  "control": {
    "error": -2.5,
    "turn": 1500,
    "base_speed": 8000
  },
  "wifi": {
    "ip": "172.20.10.4",
    "rssi": -45
  }
}
```

**使用例:**
```python
telemetry = TelemetryClient("http://192.168.1.100:8000/telemetry")
success = telemetry.send(
    sensor_values=[1,0,0,0,0,0,1,1],
    motor_left=6000,
    motor_right=8000,
    error=-2.0,
    turn=1000,
    base_speed=8000,
    network_manager=network_mgr
)
stats = telemetry.get_stats()
print(f"成功: {stats['success']}, 失敗: {stats['fail']}")
```

**特徴:**
- タイムアウト設定（デフォルト5秒）
- 自動メモリ管理（`gc.collect()`）
- 送信統計の自動記録

---

### `line_tracer.py` (5.2KB)
**ライントレース制御モジュール**

**クラス:** `LineTracer`

**主な機能:**
- `read_sensors()` - 8chセンサー読み取り
- `calculate_error()` - センサー値から誤差計算
- `set_motors()` - モーター速度設定
- `step()` - 1ステップのPD制御実行
- `stop()` - モーター停止
- `get_state()` - 現在の状態取得

**設定パラメータ:**
```python
config = {
    'sensor_pins': [22, 21, 28, 27, 26, 18, 17, 16],
    'left_fwd_pin': 5,
    'left_rev_pin': 4,
    'right_fwd_pin': 2,
    'right_rev_pin': 3,
    'base_speed': 8000,
    'left_correction': 0.77,   # 左モーター補正
    'right_correction': 1.0,   # 右モーター補正
    'kp': 9000,                # 比例ゲイン
    'kd': 3000,                # 微分ゲイン
    'weights': [-7, -5, -3, -1, 1, 3, 5, 7]  # センサー重み
}
```

**使用例:**
```python
tracer = LineTracer(config)

# メインループ
while True:
    tracer.step()  # 1ステップ実行
    state = tracer.get_state()
    print(f"エラー: {state['error']}")
    time.sleep_ms(10)

tracer.stop()  # 停止
```

**制御アルゴリズム:**
1. **センサー読み取り** - 8つのセンサーで黒ライン検出
2. **誤差計算** - 重み付き平均でライン位置を計算
3. **PD制御** - 比例・微分制御で旋回量を決定
4. **速度調整** - 誤差に応じて減速（急カーブで強く減速）
5. **モーター駆動** - 左右のモーターに異なる速度を設定

**特徴:**
- モーター補正機能（左右の速度差を補正）
- ライン未検出時の対応（前回の誤差を使用）
- PWM範囲の自動制限（0-65535）

---

## 🚀 実行方法

### 1. 設定ファイルの編集
```python
# config.py
SSID = "あなたのWiFi名"
PASSWORD = "あなたのパスワード"
SERVER_IP = "サーバーのIPアドレス"
```

### 2. Raspberry Pi Pico Wにファイルを転送
```bash
# すべてのファイルをPico Wにコピー
rshell cp src/*.py /pyboard/
```

### 3. プログラム実行
```bash
# Pico Wで実行
python main.py
```

または、`main.py`を`main.py`として保存すれば自動起動します。

---

## 📊 実行時の出力例

```
==================================================
ライントレース + テレメトリ送信（リファクタリング版）
==================================================

📡 ネットワーク初期化中...
==================================================
WiFi接続開始
==================================================
接続中: iPhone SG
✅ WiFi接続成功!
   IPアドレス: 172.20.10.4
   サーバー: http://172.20.10.3:8000/telemetry

🚗 ライントレーサー初期化中...
✅ ライントレーサー初期化完了
📊 テレメトリクライアント初期化中...

==================================================
🚀 ライントレース開始
   (Ctrl+C で停止)
==================================================
📤 送信成功 [1] | センサー: [1,1,0,0,0,1,1,1] | L:6160 R:8000 | エラー:-2.50
📤 送信成功 [2] | センサー: [1,1,1,0,0,0,1,1] | L:7200 R:7800 | エラー:-1.33
⚠️  送信失敗 [1]
...

⏹️  割り込み検出

==================================================
📊 統計情報
   送信成功: 45
   送信失敗: 3
   合計: 48
   成功率: 93.8%
==================================================
プログラム終了
==================================================
```

---

## 🔧 カスタマイズ

### 走行速度の変更
```python
# main.py
TRACER_CONFIG = {
    'base_speed': 10000,  # 速度を上げる（デフォルト: 8000）
    ...
}
```

### PD制御ゲインの調整
```python
# main.py
TRACER_CONFIG = {
    'kp': 12000,  # 比例ゲインを上げる（より敏感に）
    'kd': 4000,   # 微分ゲインを上げる（振動抑制）
    ...
}
```

### テレメトリ送信間隔の変更
```python
# main.py
TELEMETRY_INTERVAL_MS = 1000  # 1秒ごとに送信（デフォルト: 500ms）
```

---

## 🛠️ トラブルシューティング

### WiFi接続失敗
- SSIDとパスワードが正しいか確認
- iPhoneのテザリングがONになっているか確認
- 信号強度が十分か確認

### テレメトリ送信失敗
- サーバーIPアドレスが正しいか確認
- サーバーが起動しているか確認
- ファイアウォールの設定を確認

### モーターが動かない
- ピン配線が正しいか確認
- モーター補正値を調整
- PWM周波数を確認（デフォルト: 1000Hz）

---

## 📚 依存関係

- **MicroPython** (Raspberry Pi Pico W用)
- **標準ライブラリ:**
  - `machine` - ハードウェア制御
  - `network` - WiFi接続
  - `urequests` - HTTP通信
  - `ujson` - JSON処理
  - `gc` - メモリ管理
  - `time` - 時間管理

---

## 📝 ライセンス

このプロジェクトは教育目的で作成されています。

---

## 👥 作成者

4th-PBL プロジェクト

---

## 📅 更新履歴

- **2025-12-25** - モジュール化リファクタリング完了
  - `network_manager.py` 作成
  - `telemetry.py` 作成
  - `line_tracer.py` 作成
  - `main.py` を143行に簡素化

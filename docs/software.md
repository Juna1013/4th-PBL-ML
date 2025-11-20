# ソフトウェア仕様書

## 技術スタック (ソフトウェア)

- **言語**: MicroPython
- **通信プロトコル**: HTTP (REST API)
- **データ形式**: JSON

## ディレクトリ構成

- **`firmware/pico-w/`**: 本番環境用コード
  - `main.py`: 統合制御プログラム
  - `config.py`: 設定ファイル（WiFi, サーバーURLなど）
  - `wifi_client.py`: HTTP通信クライアント
  - `motor_control.py`: モーター制御クラス
  - `line_trace_controller.py`: ライントレースロジック
  - `sensors.py`: センサー管理クラス
- **`firmware/test/`**: テスト用コード
  - `integration_test/`: 統合テスト
  - `unit_test/`: 単体テスト

## ソフトウェアアーキテクチャ

システムは以下のクラスで構成され、責務が分離されています。

- **`PicoWController`**: システム全体を統括するメインクラス。WiFi接続、コマンド処理、メインループの制御を行います。
- **`WiFiClient`**: WiFi接続の確立・維持と、サーバーとのHTTP通信（GET/POST）を担当します。
- **`MotorController`**: モータードライバ（MakerDrive）の制御を行います。通常走行とライントレース走行の両方のロジックを管理します。
- **`LineTraceController`**: ライントレースのコアロジック（センサー値の読み取り、ライン位置の計算、PID制御による操作量の算出）を担当します。
- **`PhotoReflector`**: 8個のフォトリフレクタセンサーの値を読み取り、正規化されたデータを提供します。

## サーバー通信仕様

通常モードでは、以下のAPIエンドポイントを使用してサーバーと通信します。

### 1. コマンド取得

- **Endpoint**: `GET /api/command/latest`
- **Response**:
  ```json
  {
    "command": "FORWARD",  // FORWARD, BACK, LEFT, RIGHT, STOP, LINE_TRACE
    "timestamp": 1678888888
  }
  ```

### 2. ステータス送信

- **Endpoint**: `POST /api/pico/status`
- **Body**:
  ```json
  {
    "status": "running",
    "sensor_values": [0, 0, 1, 1, 0, 0, 0, 0],
    "battery_level": 85
  }
  ```

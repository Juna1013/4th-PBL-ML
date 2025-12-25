# テレメトリシステム

ラズピコWからセンサーとモーターの状態を外部サーバーにリアルタイムで送信するシステム

## 構成

### 1. ラズピコW側プログラム
**ファイル**: `test/integration_test/test_02_with_telemetry.py`

ライントレースを実行しながら、以下のデータを定期的にサーバーに送信：
- センサー値（8個のラインセンサー）
- モーター速度（左右）
- 制御パラメータ（エラー値、ターン値）
- WiFi情報（IPアドレス、信号強度）

### 2. サーバー側プログラム
**ファイル**: `server/telemetry_server.py`

テレメトリデータを受信・表示・保存するFlaskサーバー

## セットアップ

### 1. config.pyの準備

`firmware/config.py`を作成（まだ存在しない場合）：

```python
# WiFi設定
SSID = "your_wifi_ssid"
PASSWORD = "your_wifi_password"

# サーバー設定
SERVER_IP = "192.168.1.100"  # サーバーのIPアドレス
```

### 2. サーバー側の準備

```bash
# 必要なパッケージをインストール
pip install flask

# サーバーを起動
cd firmware/server
python telemetry_server.py
```

サーバーが起動したら、表示されるIPアドレスを`config.py`の`SERVER_IP`に設定してください。

### 3. ラズピコWへのデプロイ

1. `test_02_with_telemetry.py`と`config.py`をラズピコWにコピー
2. ラズピコWで実行：
   ```python
   import test_02_with_telemetry
   ```

## 送信データ形式

```json
{
  "timestamp": 12345,
  "sensors": [1, 1, 0, 0, 0, 1, 1, 1],
  "motor": {
    "left_speed": 6160,
    "right_speed": 8000
  },
  "control": {
    "error": -1.5,
    "turn": -10500,
    "base_speed": 8000
  },
  "wifi": {
    "ip": "192.168.1.101",
    "rssi": -45
  }
}
```

## サーバーエンドポイント

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/ping` | 接続テスト |
| POST | `/telemetry` | テレメトリデータ受信 |
| GET | `/telemetry/latest` | 最新データ取得 |
| GET | `/telemetry/history?count=10` | 履歴取得 |
| GET | `/telemetry/export` | データエクスポート |
| POST | `/telemetry/clear` | 履歴クリア |

## パラメータ調整

### 送信間隔の変更

`test_02_with_telemetry.py`の33行目：
```python
TELEMETRY_INTERVAL_MS = 500  # ミリ秒単位（500ms = 0.5秒）
```

- **高頻度送信**: `200`〜`300`（より詳細なデータ、WiFi負荷増）
- **低頻度送信**: `1000`〜`2000`（WiFi負荷軽減、データ粗め）

### サーバーポートの変更

両方のファイルで同じポート番号を使用してください：
- `telemetry_server.py`: 最終行の`port=8000`
- `test_02_with_telemetry.py`: 34行目の`:8000`

## トラブルシューティング

### WiFi接続できない
- `config.py`のSSIDとパスワードを確認
- WiFiルーターの2.4GHz帯を使用（ラズピコWは5GHz非対応）

### サーバーに接続できない
- サーバーのIPアドレスが正しいか確認
- ファイアウォールで8000番ポートが開いているか確認
- サーバーとラズピコWが同じネットワークにいるか確認

### データが送信されない
- サーバーのログを確認
- ラズピコWのコンソール出力を確認
- `TELEMETRY_INTERVAL_MS`が適切か確認

## 今後の拡張案

- [ ] WebSocketによるリアルタイム双方向通信
- [ ] Webダッシュボードでのデータ可視化
- [ ] データベースへの永続化
- [ ] アラート機能（異常検知時の通知）
- [ ] リモート制御機能（パラメータの動的変更）

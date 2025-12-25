# ファームウェア - API統合ガイド

## 概要

このガイドでは、Raspberry Pi Pico Wのファームウェアから、Next.jsで構築されたWebサーバーにセンサーデータを送信する方法を説明します。

## セットアップ手順

### 1. 設定ファイルの作成

`config.example.py`をコピーして`config.py`を作成し、環境に合わせて編集します。

```bash
cp config.example.py config.py
```

`config.py`の内容を編集：

```python
# WiFi設定
SSID = "your-wifi-ssid"          # 実際のWiFi SSID
PASSWORD = "your-wifi-password"   # 実際のWiFiパスワード

# サーバー設定
SERVER_IP = "192.168.1.100"       # Next.jsサーバーのIPアドレス
SERVER_PORT = 3000                # 通常は3000
```

### 2. Next.jsサーバーのIPアドレスを確認

Next.jsサーバーを起動すると、以下のように表示されます：

```
▲ Next.js 16.1.0 (Turbopack)
- Local:         http://localhost:3000
- Network:       http://192.168.3.171:3000
```

`Network`に表示されているIPアドレス（例: `192.168.3.171`）を`config.py`の`SERVER_IP`に設定してください。

### 3. ファームウェアのアップロード

1. Raspberry Pi Pico Wをパソコンに接続
2. Thonnyなどのエディタで`line_trace_with_api.py`を開く
3. Pico Wにアップロード

### 4. 動作確認

#### サーバー側

```bash
cd web
npm run dev
```

ブラウザで`http://localhost:3000`を開き、「リアルタイムデータ (SSE)」ボタンをクリック。

#### ファームウェア側

Pico Wでプログラムを実行：

```python
# Thonnyで line_trace_with_api.py を実行
```

コンソールに以下のように表示されれば成功：

```
=== WiFi接続開始 ===
WiFi接続完了: 192.168.3.XXX
サーバー応答: {"status":"ok","message":"Server is running","timestamp":...}
=== ライントレース + API送信開始 ===
```

## API エンドポイント

### 1. Ping（接続確認）

**エンドポイント**: `GET /api/ping`

**レスポンス**:
```json
{
  "status": "ok",
  "message": "Server is running",
  "timestamp": 1703251200000
}
```

### 2. センサーデータ送信

**エンドポイント**: `POST /api/sensor`

**リクエストボディ**:
```json
{
  "timestamp": 1703251200000,
  "sensors": {
    "values": [0, 0, 1, 1, 1, 1, 0, 0],
    "lineDetected": true
  },
  "motors": {
    "left": {
      "speed": 10000,
      "direction": "forward"
    },
    "right": {
      "speed": 12000,
      "direction": "forward"
    }
  },
  "error": -2.5,
  "status": "running"
}
```

**レスポンス**:
```json
{
  "status": "ok",
  "message": "Data received",
  "timestamp": 1703251200000
}
```

### 3. リアルタイムストリーム（SSE）

**エンドポイント**: `GET /api/stream`

**レスポンス**: Server-Sent Events形式

```
data: {"type":"connected","message":"Stream connected","timestamp":...}

data: {"type":"sensor_data","data":{...},"timestamp":...}

data: {"type":"sensor_data","data":{...},"timestamp":...}
```

## データフロー

```
[Pico W] センサー読み取り
    ↓
[Pico W] WiFi経由でPOST /api/sensor
    ↓
[Next.js] データを受信・保存
    ↓
[Next.js] SSE経由でブラウザに配信
    ↓
[ブラウザ] リアルタイム表示
```

## トラブルシューティング

### WiFi接続できない

- SSIDとパスワードが正しいか確認
- Pico WとNext.jsサーバーが同じネットワークに接続されているか確認

### サーバーに接続できない

- `SERVER_IP`が正しいか確認（`ifconfig`や`ipconfig`で確認）
- ファイアウォールでポート3000が開いているか確認
- Next.jsサーバーが起動しているか確認

### データが表示されない

- ブラウザで「リアルタイムデータ (SSE)」モードになっているか確認
- ブラウザの開発者ツール（F12）でネットワークタブを確認
- サーバーのコンソールログを確認

## 開発モード

実機がない場合は、「モックデータ」モードで動作確認できます。

ブラウザで「モックデータ」ボタンをクリックすると、ランダムなセンサーデータが生成されます。

## 参考

- [Next.js API Routes](https://nextjs.org/docs/app/building-your-application/routing/route-handlers)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [MicroPython urequests](https://docs.micropython.org/en/latest/library/urequests.html)

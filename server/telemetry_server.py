"""
ラズピコWからのテレメトリデータを受信するサーバー
センサーとモーターの状態をリアルタイムで表示・保存
"""

from flask import Flask, request, jsonify, render_template
from datetime import datetime
import json

app = Flask(__name__)

# テレメトリデータを保存するリスト（最新100件）
telemetry_history = []
MAX_HISTORY = 100

@app.route('/')
def dashboard():
    """ダッシュボードページを表示"""
    return render_template('dashboard.html')

@app.route('/ping', methods=['GET'])
def ping():
    """接続テスト用エンドポイント"""
    return jsonify({"status": "ok", "message": "Server is running"})

@app.route('/telemetry', methods=['POST'])
def receive_telemetry():
    """テレメトリデータを受信"""
    try:
        data = request.get_json()
        
        # タイムスタンプを追加
        data['server_timestamp'] = datetime.now().isoformat()
        
        # 履歴に追加
        telemetry_history.append(data)
        if len(telemetry_history) > MAX_HISTORY:
            telemetry_history.pop(0)
        
        # コンソールに表示
        print(f"\n{'='*60}")
        print(f"受信時刻: {data['server_timestamp']}")
        
        # データ形式を判定して表示
        if 'sensors' in data:
            # test_02_with_telemetry.py形式
            print(f"センサー値: {data['sensors']}")
            if 'motor' in data:
                print(f"左モーター速度: {data['motor']['left_speed']}")
                print(f"右モーター速度: {data['motor']['right_speed']}")
            if 'control' in data:
                print(f"エラー値: {data['control']['error']:.2f}")
                print(f"ターン値: {data['control']['turn']}")
            if 'wifi' in data:
                print(f"WiFi IP: {data['wifi']['ip']}")
        elif 'sensor_values' in data:
            # test_02.py形式
            print(f"センサー値: {data['sensor_values']}")
            print(f"黒線検出数: {data.get('black_detected', 'N/A')}")
            print(f"センサーパターン: {data.get('sensor_binary', 'N/A')}")
            print(f"タイムスタンプ: {data.get('timestamp', 'N/A')}")
        
        print(f"{'='*60}")
        
        return jsonify({"status": "success", "received": True}), 200
        
    except Exception as e:
        print(f"エラー: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/telemetry/latest', methods=['GET'])
def get_latest_telemetry():
    """最新のテレメトリデータを取得"""
    if telemetry_history:
        return jsonify(telemetry_history[-1])
    else:
        return jsonify({"status": "no_data"}), 404

@app.route('/telemetry/history', methods=['GET'])
def get_telemetry_history():
    """テレメトリ履歴を取得"""
    count = request.args.get('count', default=10, type=int)
    count = min(count, len(telemetry_history))
    return jsonify(telemetry_history[-count:])

@app.route('/telemetry/export', methods=['GET'])
def export_telemetry():
    """テレメトリデータをJSON形式でエクスポート"""
    filename = f"telemetry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(telemetry_history, f, indent=2, ensure_ascii=False)
    
    return jsonify({
        "status": "success",
        "filename": filename,
        "count": len(telemetry_history)
    })

@app.route('/telemetry/clear', methods=['POST'])
def clear_telemetry():
    """テレメトリ履歴をクリア"""
    global telemetry_history
    count = len(telemetry_history)
    telemetry_history = []
    return jsonify({"status": "success", "cleared": count})

if __name__ == '__main__':
    print("="*60)
    print("テレメトリサーバー起動")
    print("ポート: 8000")
    print("エンドポイント:")
    print("  GET  / - ダッシュボード（ブラウザで開く）")
    print("  GET  /ping - 接続テスト")
    print("  POST /telemetry - テレメトリデータ受信")
    print("  GET  /telemetry/latest - 最新データ取得")
    print("  GET  /telemetry/history?count=10 - 履歴取得")
    print("  GET  /telemetry/export - データエクスポート")
    print("  POST /telemetry/clear - 履歴クリア")
    print("="*60)
    
    # 0.0.0.0でリッスンして、ネットワーク上の他のデバイスからアクセス可能に
    app.run(host='0.0.0.0', port=8000, debug=True)

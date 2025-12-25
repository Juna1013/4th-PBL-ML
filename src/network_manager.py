'''
WiFi接続とネットワーク管理モジュール
'''

import network
import time
from machine import Pin

class NetworkManager:
    """WiFi接続を管理するクラス"""
    
    def __init__(self, ssid, password, led_pin="LED", timeout=30):
        """
        Args:
            ssid: WiFi SSID
            password: WiFiパスワード
            led_pin: 接続状態表示用LEDピン
            timeout: 接続タイムアウト（秒）
        """
        self.ssid = ssid
        self.password = password
        self.timeout = timeout
        self.wlan = None
        self.led = Pin(led_pin, Pin.OUT)
        self.led.value(0)
    
    def connect(self):
        """WiFiに接続（タイムアウト付き）"""
        print("=" * 50)
        print("WiFi接続開始")
        print("=" * 50)
        
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
        if not self.wlan.isconnected():
            print(f"接続中: {self.ssid}")
            self.wlan.connect(self.ssid, self.password)
            
            # 接続を最大timeout秒待機
            timeout_counter = self.timeout
            while not self.wlan.isconnected() and timeout_counter > 0:
                print(".", end="")
                time.sleep(1)
                timeout_counter -= 1
                self.led.toggle()
            
            print()
        
        if self.wlan.isconnected():
            ip = self.wlan.ifconfig()[0]
            print(f"✅ WiFi接続成功!")
            print(f"   IPアドレス: {ip}")
            self.led.value(1)
            return True
        else:
            print("❌ WiFi接続失敗")
            self.led.value(0)
            return False
    
    def disconnect(self):
        """WiFi接続を切断"""
        if self.wlan:
            self.wlan.disconnect()
            self.wlan.active(False)
            self.led.value(0)
            print("WiFi切断")
    
    def get_ip(self):
        """IPアドレスを取得"""
        if self.wlan and self.wlan.isconnected():
            return self.wlan.ifconfig()[0]
        return None
    
    def get_rssi(self):
        """信号強度を取得"""
        if self.wlan and hasattr(self.wlan, 'status'):
            return self.wlan.status('rssi')
        return None
    
    def is_connected(self):
        """接続状態を確認"""
        return self.wlan and self.wlan.isconnected()

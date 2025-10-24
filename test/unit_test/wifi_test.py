import network
import time
import urequests
from machine import Pin

# 設定
SSID = "自分のWiFiのSSID"
PASSWORD = "自分のWiFiのパスワード"

TEST_URL = "http://example.com"

led = Pin("LED", Pin.OUT)

# WiFi接続関数
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
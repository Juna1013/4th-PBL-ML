import network
import time
import urequests
import config

# WiFi接続
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config.SSID, config.PASSWORD)

while not wlan.isconnected():
    print("Connected...")
    time.sleep(1)
print("Connected:", wlan.ifconfig()[0])

# サーバーへのアクセス
url = f"http://{config.SERVER_IP}:8000/ping"
res = urequests.get(url)
print(res.text)
res.close()

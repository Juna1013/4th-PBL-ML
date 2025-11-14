import network
import time
import urequests

SSID = 'Juna1013'
PW = 'f94s7uu4'

# WiFi接続
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PW)

while wlan.isconnected() == False:
    print('Connecting to Wi-Fi router')
    time.sleep(1)

ip_info = wlan.ifconfig()
print("Connected!")
print("IP Adress:", ip_info[0])
PORT = 8000

# FastAPIサーバーにアクセス
SERVER_IP = "10.73.246.50"
PORT = 8000

try:
    url = f"http://{SERVER_IP}:{PORT}/ping"
    print("Requesting:", url)
    response = urequests.get(url)
    print("Response:", response.text)
    response.close()
except Exceprion as e:
    print("Error:", e)

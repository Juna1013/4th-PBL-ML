import network
import time
SSID = 'Juna1013'
PW = 'f94s7uu4'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PW)

while wlan.isconnected() == False:
    print('Connecting to Wi-Fi router')
    time.sleep(1)

wlan_status = wlan.ifconfig()
print('Connected')
print(f'IP Adress: {wlan_status[0]}')
print(f'Netmask: {wlan_status[1]}')
print(f'Default Gateway: {wlan_status[2]}')
print(f'Name Server: {wlan_status[3]}')

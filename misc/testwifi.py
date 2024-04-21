import time
import ntptime
import network


NIC = network.WLAN(network.STA_IF)


# turn on wifi if it isn't already
if not NIC.active():
    NIC.active(True)
    
print(NIC.scan())
    
    
# # try connecting
# if not NIC.isconnected():
#     try:
#         NIC.connect(CONFIG['wifi_ssid'], CONFIG['wifi_pass'])
#     except OSError as e:
#         print("wifi_sync_rtc had this error when connecting:", e)
# 
# 
# 
# 
# ntptime.settime()
# 
# NIC.disconnect()
# NIC.active(False)
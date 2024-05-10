from data_parser import NIC, connect_to_internet, stop_internet_connection, CONFIG
import time

num_scans = 3

SSID = CONFIG['wifi_creds'][0][0]
results = []


NIC.active(1)


for i in range(num_scans):
    scan = NIC.scan()
    for item in scan:
        name = item[0].decode()
        if name == SSID:
            results.append(item[3])
            
print(results)

avg = sum(results) / len(results)
print(f"Signal strength for '{SSID}': {avg}")


NIC.active(0)
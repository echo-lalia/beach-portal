import machine, time
from machine import Pin, ADC


sensor = ADC(17)
sensor_hist = []



def read_sensor():
    _HIST_LEN = const(100)
    _SENSOR_MIN = const(1000)
    _SENSOR_MAX = const(65535)
    _SENSOR_RANGE = const(_SENSOR_MAX - _SENSOR_MIN)
    
    global sensor_hist
    
    sensor_hist.append(sensor.read_u16())
    
    if len(sensor_hist) > _HIST_LEN:
        sensor_hist.pop(0)
        
    avg_reading = sum(sensor_hist) / len(sensor_hist)
    
    avg_reading -= _SENSOR_MIN
    if avg_reading < 0:
        avg_reading = 0
    
    return avg_reading / _SENSOR_RANGE


while True:
    print(read_sensor())
    time.sleep(0.1)


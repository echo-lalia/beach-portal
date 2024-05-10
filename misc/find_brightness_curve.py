from machine import ADC, Pin, PWM


_HIST_LEN = const(500)
_SENSOR_MIN = const(0)
_SENSOR_MAX = const(65535)
_SENSOR_RANGE = const(_SENSOR_MAX - _SENSOR_MIN)


class LightSensor:
    
    def __init__(self):
        
        self.adc = ADC(17)
        self.hist = []
    
    def read(self) -> float:
        
        # take a couple of samples for our reading, for accuracy
        one_reading = (self.adc.read_u16() + self.adc.read_u16()) // 2
        self.hist.append(one_reading)
        
        if len(self.hist) > _HIST_LEN:
            self.hist.pop(0)
            
        return sum(self.hist) / len(self.hist)


if __name__ == "__main__":
    
    blight_brightness = 1_000
    
    import time
    
    sensor = LightSensor()
    max_seen = 0
    
    BLIGHT = PWM(Pin(1, Pin.OUT))
    
    BLIGHT.duty_u16(blight_brightness)
    for _ in range(_HIST_LEN):
        time.sleep_ms(1)
        sensor.read()
        
    print("Light level for brightness:")
    print(f"({sensor.read()}, {blight_brightness}),")
    
    time.sleep(2)

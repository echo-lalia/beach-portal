from machine import ADC


_HIST_LEN = const(100)
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
            
        avg_reading = sum(self.hist) / len(self.hist)
        
        avg_reading -= _SENSOR_MIN
        if avg_reading < 0:
            avg_reading = 0
        
        return avg_reading / _SENSOR_RANGE
    
    
    
    def infer_motion_level(self):
        """
        Use light sensor to infer motion by comparing minimum and maximum readings.
        """
        _MOTION_SAMPLES = const(3)
        _MINIMUM_MOTION_LEN = const(_MOTION_SAMPLES * 2)
        
        # cant infer motion with too few samples
        if len(self.hist) < _MINIMUM_MOTION_LEN:
            return 0.0
        
        # make copy of list to work with
        working_list = self.hist.copy()
        working_list.sort()
        
        # slice min and max vals from working list, and average them.
        minimum = sum(working_list[:_MOTION_SAMPLES]) / _MOTION_SAMPLES
        maximum = sum(working_list[-_MOTION_SAMPLES : len(working_list)]) / _MOTION_SAMPLES
        
        
        return abs((maximum - minimum) / _SENSOR_RANGE)

if __name__ == "__main__":
    import time
    
    sensor = LightSensor()
    
    while True:
        print(f"{round(sensor.read(), 2)}, motion level: {round(sensor.infer_motion_level(), 2)}")
        time.sleep_ms(10)
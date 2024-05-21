from machine import ADC


_HIST_LEN = const(400)
# _SENSOR_MIN = const(0)
# #_SENSOR_MAX = const(65535)
# _SENSOR_MAX = const(1000) # temporary val; must be changed as hardware changes
#_SENSOR_RANGE = const(_SENSOR_MAX - _SENSOR_MIN)

# # these values were calculated using testing + numpy polyfit
# _SENSOR_POLYNOMIAL_DEF = [ 4.76817472e-06, -1.34239464e-02,  1.91396095e+01, -1.74166094e+03]
# #_SENSOR_POLYNOMIAL_DEF = [4.76817472e-06, -0.01342395,  19.13961, -1742]
# # polynomial order needs to be reversed for the below function
# #_SENSOR_POLYNOMIAL_DEF = list(reversed(_SENSOR_POLYNOMIAL_DEF))
_DEFAULT_MIN_READING = const(500)
_ABSOLUTE_MIN_READING = const(200)
_MAX_READING = const(3000)
#_SENSOR_RANGE = const(_MIN_READING - _MAX_READING)

class LightSensor:
    
    def __init__(self):
        
        self.adc = ADC(17)
        self.hist = []
        self.min_reading = _DEFAULT_MIN_READING
        
        
    def transform_input(self, x):
        if x >= _MAX_READING:
            return 65535
        
        minimum = self.min_reading
        
        x -= minimum
        if x < 0:
            x = 0
        
        sensor_range = _MAX_READING - minimum
        x /= sensor_range
        
        return int(x * 65535)
    
    
    
    def read(self):
        
        one_reading = self.adc.read_u16()
        self.hist.append(one_reading)
        
        if len(self.hist) > _HIST_LEN:
            self.hist.pop(0)

        avg_reading = sum(self.hist) / len(self.hist)
        
        # remember min reading
        if avg_reading < self.min_reading\
           and len(self.hist) == _HIST_LEN:
            self.min_reading = max(avg_reading, _ABSOLUTE_MIN_READING)
            print('min_reading:', self.min_reading)
            
        if avg_reading < self.min_reading + 5:
            return 0
        if avg_reading > _MAX_READING:
            # reset min_reading to default value if its bright
            # (so that it will be re-calibrated next time it's dark)
            self.min_reading = _DEFAULT_MIN_READING
            return 65535
        
        return self.transform_input(avg_reading)
    
    
    
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
        
        sensor_range = _MAX_READING - self.min_reading
        return abs((maximum - minimum) / sensor_range)



if __name__ == "__main__":
    import time
    
    sensor = LightSensor()
    max_seen = 0
    while True:
        #sensor.read()
        print(f"{round(sensor.read(), 4)}, motion level: {round(sensor.infer_motion_level(), 2)}")
#         read = sensor.read()
#         if read > max_seen:
#             max_seen = read
#             print(f"Max level seen: {max_seen}")
        time.sleep_ms(10)
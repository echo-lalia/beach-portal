import time

def log(log_text):
    year, month, day, hour, minute, *_ = time.localtime()
    log_str = f"""[{hour}:{minute} {year}/{month}/{day}]
  - {log_text}
"""
    try:
        with open('/log.txt', 'a') as log_file:
            log_file.write(log_str)
    except Exception as e:
        print(f"Logging failed: {e}")
        print("Assuming file is too big and erasing.")
        os.remove("/log.txt")

    print(log_str)

def clamp(value, minimum=0, maximum=1):
    if value < minimum:
        value = minimum
    if value > maximum:
        value = maximum
    return value

def get_factor(minimum, current, maximum) -> float:
    """Calculate where "current" falls between minimum/maximum,
    returns a float from 0.0 to 1.0
    """
    
    if current >= maximum:
        return 1.0
    if current <= minimum:
        return 0.0
    
    # rescale vals so that minimum = 0
    current = current - minimum
    maximum = maximum - minimum
    
    return current / maximum

def swap_bytes(color):
    """
    this just flips the left and right byte in the 16 bit color.
    """
    return ((color & 255) << 8) + (color >> 8)

def remap(value, in_min, in_max, clamp=True):
    if clamp == True:
        if value < in_min:
            return 0.0
        elif value > in_max:
            return 1.0
    # Scale the value to be in the range 0.0 to 1.0
    return (value - in_min) / (in_max - in_min)


def ping_pong(value,maximum):
    odd_pong = (int(value / maximum) % 2 == 1)
    mod = value % maximum
    if odd_pong:
        return maximum - mod
    else:
        return mod

def mix(val2, val1, factor=0.5):
    """Mix two values to the weight of fac"""
    output = (val1 * factor) + (val2 * (1.0 - factor))
    return output

def separate_color565(color):
    """
    Separate a 16-bit 565 encoding into red, green, and blue components.
    """
    red = (color >> 11) & 0x1F
    green = (color >> 5) & 0x3F
    blue = color & 0x1F
    return red, green, blue


def combine_color565(red, green, blue):
    """
    Combine red, green, and blue components into a 16-bit 565 encoding.
    """
    # Ensure color values are within the valid range
    red = max(0, min(red, 31))
    green = max(0, min(green, 63))
    blue = max(0, min(blue, 31))

    # Pack the color values into a 16-bit integer
    return (red << 11) | (green << 5) | blue
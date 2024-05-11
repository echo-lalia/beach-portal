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
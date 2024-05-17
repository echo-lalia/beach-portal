from utils import *


# rgb565
color1 = 33897
color2 = 62975
color3 = 12964
color4 = 38392

def overlay_val_float(a,b):
    if a < 0.5:
        return 2 * a * b
    else:
        return 1 - (2 * (1 - a) * (1 - b))
        

def overlay_floats(clr1, clr2):
    r1,g1,b1 = separate_color565(clr1)
    r2,g2,b2 = separate_color565(clr2)
    
    r1 /= 31; g1 /= 63; b1 /= 31
    r2 /= 31; g2 /= 63; b2 /= 31
    
    red = overlay_val_float(r1, r2)
    green = overlay_val_float(g1, g2)
    blue = overlay_val_float(b1, b2)
    
    red *= 31
    green *= 63
    blue *= 31
    
    return combine_color565(
        int(red),
        int(green),
        int(blue))


def overlay_val_int(a,b,divisor):
    if a < (divisor // 2):
        return (2 * a * b) // divisor
    else:
        # invert colors
        a = divisor - a
        b = divisor - b
        # multiply
        output = (2 * a * b) // divisor
        #uninvert output
        output = divisor - output
        return output


def overlay_ints(clr1, clr2):
    r1,g1,b1 = separate_color565(clr1)
    r2,g2,b2 = separate_color565(clr2)
    
    red = overlay_val_int(r1, r2, 31)
    green = overlay_val_int(g1, g2, 63)
    blue = overlay_val_int(b1, b2, 31)
    
    return combine_color565(
        (red),
        (green),
        (blue))


@micropython.viper
def overlay_viper(clr1:int, clr2:int) -> int:
    # separate rgb565
    r1 = (clr1 >> 11) & 0x1F
    g1 = (clr1 >> 5) & 0x3F
    b1 = clr1 & 0x1F
    
    r2 = (clr2 >> 11) & 0x1F
    g2 = (clr2 >> 5) & 0x3F
    b2 = clr2 & 0x1F
    
    # preform overlay math on each component pair
    # this would be better to read if it were separated to another function,
    # however it's faster if it's all inline
    
    divisor = 31
    if r1 < (divisor // 2):
        red = (2 * r1 * r2) // divisor
    else:
        # invert colors
        r1 = divisor - r1
        r2 = divisor - r2
        # multiply
        output = (2 * r1 * r2) // divisor
        #uninvert output
        output = divisor - output
        red = output
    
    divisor = 63
    if g1 < (divisor // 2):
        green = (2 * g1 * g2) // divisor
    else:
        # invert colors
        g1 = divisor - g1
        g2 = divisor - g2
        # multiply
        output = (2 * g1 * g2) // divisor
        #uninvert output
        output = divisor - output
        green = output
    
    divisor = 31
    if b1 < (divisor // 2):
        blue = (2 * b1 * b2) // divisor
    else:
        # invert colors
        b1 = divisor - b1
        b2 = divisor - b2
        # multiply
        output = (2 * b1 * b2) // divisor
        #uninvert output
        output = divisor - output
        blue = output
    
    # combine color565
    return (red << 11) | (green << 5) | blue
    
print(
f"""
-----------------------------------------------
color1 = {color1} # {separate_color565(color1)}
color2 = {color2} # {separate_color565(color2)}
color3 = {color3} # {separate_color565(color3)}
color4 = {color4} # {separate_color565(color4)}
-----------------------------------------------

overlay_floats(color1, color2):
{overlay_floats(color1, color2)} # {separate_color565(overlay_floats(color1, color2))}

overlay_ints(color1, color2):
{overlay_ints(color1, color2)} # {separate_color565(overlay_ints(color1, color2))}

-----------------------------------------------

overlay_floats(color3, color4):
{overlay_floats(color3, color4)} # {separate_color565(overlay_floats(color3, color4))}

overlay_ints(color3, color4):
{overlay_ints(color3, color4)} # {separate_color565(overlay_ints(color3, color4))}

overlay_viper(color3, color4):
{overlay_viper(color3, color4)} # {separate_color565(overlay_viper(color3, color4))}

-----------------------------------------------
"""
)
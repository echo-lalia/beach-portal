from utils import *


# rgb565
color1 = 33897
color2 = 62975


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
    
    print('floats:', red, green, blue)
    
    return combine_color565(
        int(red),
        int(green),
        int(blue))


def overlay_val_int(a,b,divisor):
    if a < (divisor // 2):
        return (a * b) // divisor
    else:
        return - divisor + (2*b) + (2*a) - ((2*a*b) // divisor)
        # -31 + (2*b) + (2*a) - ((2*a*b)/31)
        #return divisor - ((divisor - a) * (divisor - b) // divisor)
    
def overlay_ints(clr1, clr2):
    r1,g1,b1 = separate_color565(clr1)
    r2,g2,b2 = separate_color565(clr2)
    
    red = overlay_val_int(r1, r2, 31)
    green = overlay_val_int(g1, g2, 63)
    blue = overlay_val_int(b1, b2, 31)
    
    print('ints:', red, green, blue)
    
    return combine_color565(
        (red),
        (green),
        (blue))


def overlay_ints_higher(clr1, clr2):
    _DIVISOR = const(1024)
    r1,g1,b1 = separate_color565(clr1)
    r2,g2,b2 = separate_color565(clr2)
    
    # multiply integers to get higher accuracy output
    red = overlay_val_int(r1 * _DIVISOR, r2 * _DIVISOR, 31 * _DIVISOR) // _DIVISOR
    green = overlay_val_int(g1 * _DIVISOR, g2 * _DIVISOR, 63 * _DIVISOR) // _DIVISOR
    blue = overlay_val_int(b1 * _DIVISOR, b2 * _DIVISOR, 31 * _DIVISOR) // _DIVISOR
    
    print('bigints:', red, green, blue)
    
    return combine_color565(
        (red),
        (green),
        (blue))

@micropython.viper
def overlay_vals_viper(a:int,b:int,divisor:int) -> int:
    if a < (divisor // 2):
        return (a * b) // divisor
    else:
        return (divisor - ((divisor - a) * (divisor - b)) // divisor)

@micropython.viper
def overlay_ints_viper(clr1:int, clr2:int) -> int:
    # separate 565 color
    r1 = ((clr1 >> 11) & 0x1F)
    g1 = ((clr1 >> 5) & 0x3F)
    b1 = (clr1 & 0x1F)
    
    r2 = ((clr2 >> 11) & 0x1F)
    g2 = ((clr2 >> 5) & 0x3F)
    b2 = (clr2 & 0x1F)
  
    # preform overlay math on red/green/blue channels
    # vals are multiplied by 8 for higher accuracy.
    y = 31
    if r1 < (15):
        red = (r1 * r2) // y
    else:
        red = ((r1*y) + (r2*y) - (r1*r2)) // y
    
    y = 63
    if g1 < (31):
        green = (g1 * g2) // y
    else:
        green = ((g1*y) + (g2*y) - (g1*g2)) // y
        
    y = 31
    if b1 < (15):
        blue = (b1 * b2) // y
    else:
        blue = ((b1*y) + (b2*y) - (b1*b2)) // y
    
    
    print("viper:",red,green,blue)
    
    return (red << 11) | (green << 5) | blue

print(overlay_floats(color1, color2))
print(overlay_ints(color1, color2))
print(overlay_ints_higher(color1, color2))
print(overlay_ints_viper(color1, color2))
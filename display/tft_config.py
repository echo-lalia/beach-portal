import rm67162
from machine import Pin, SPI
import time

# I do not know what any of the commands do. I pulled them from here:
# https://github.com/moononournation/Arduino_GFX/blob/master/src/display/Arduino_NV3041A.h
_NV3041A_INIT_CMDS = const((
    (b'\xff', b'\xa5', 0),
    (b'6', b'\xc0', 0),
    (b':', b'\x01', 0),
    (b'A', b'\x03', 0),
    (b'D', b'\x15', 0),
    (b'E', b'\x15', 0),
    (b'}', b'\x03', 0),
    (b'\xc1', b'\xbb', 0),
    (b'\xc2', b'\x05', 0),
    (b'\xc3', b'\x10', 0),
    (b'\xc6', b'>', 0),
    (b'\xc7', b'%', 0),
    (b'\xc8', b'\x11', 0),
    (b'z', b'_', 0),
    (b'o', b'D', 0),
    (b'x', b'p', 0),
    (b'\xc9', b'\x00', 0),
    (b'g', b'!', 0),
    (b'Q', b'\n', 0),
    (b'R', b'v', 0),
    (b'S', b'\n', 0),
    (b'T', b'v', 0),
    (b'F', b'\n', 0),
    (b'G', b'*', 0),
    (b'H', b'\n', 0),
    (b'I', b'\x1a', 0),
    (b'V', b'C', 0),
    (b'W', b'B', 0),
    (b'X', b'<', 0),
    (b'Y', b'd', 0),
    (b'Z', b'A', 0),
    (b'[', b'<', 0),
    (b'\\', b'\x02', 0),
    (b']', b'<', 0),
    (b'^', b'\x1f', 0),
    (b'`', b'\x80', 0),
    (b'a', b'?', 0),
    (b'b', b'!', 0),
    (b'c', b'\x07', 0),
    (b'd', b'\xe0', 0),
    (b'e', b'\x02', 0),
    (b'\xca', b' ', 0),
    (b'\xcb', b'R', 0),
    (b'\xcc', b'\x10', 0),
    (b'\xcd', b'B', 0),
    (b'\xd0', b' ', 0),
    (b'\xd1', b'R', 0),
    (b'\xd2', b'\x10', 0),
    (b'\xd3', b'B', 0),
    (b'\xd4', b'\n', 0),
    (b'\xd5', b'2', 0),
    (b'\x80', b'\x00', 0),
    (b'\xa0', b'\x00', 0),
    (b'\x81', b'\x07', 0),
    (b'\xa1', b'\x06', 0),
    (b'\x82', b'\x02', 0),
    (b'\xa2', b'\x01', 0),
    (b'\x86', b'\x11', 0),
    (b'\xa6', b'\x10', 0),
    (b'\x87', b"'", 0),
    (b'\xa7', b"'", 0),
    (b'\x83', b'7', 0),
    (b'\xa3', b'7', 0),
    (b'\x84', b'5', 0),
    (b'\xa4', b'5', 0),
    (b'\x85', b'?', 0),
    (b'\xa5', b'?', 0),
    (b'\x88', b'\x0b', 0),
    (b'\xa8', b'\x0b', 0),
    (b'\x89', b'\x14', 0),
    (b'\xa9', b'\x14', 0),
    (b'\x8a', b'\x1a', 0),
    (b'\xaa', b'\x1a', 0),
    (b'\x8b', b'\n', 0),
    (b'\xab', b'\n', 0),
    (b'\x8c', b'\x14', 0),
    (b'\xac', b'\x08', 0),
    (b'\x8d', b'\x17', 0),
    (b'\xad', b'\x07', 0),
    (b'\x8e', b'\x16', 0),
    (b'\xae', b'\x06', 0),
    (b'\x8f', b'\x1b', 0),
    (b'\xaf', b'\x07', 0),
    (b'\x90', b'\x04', 0),
    (b'\xb0', b'\x04', 0),
    (b'\x91', b'\n', 0),
    (b'\xb1', b'\n', 0),
    (b'\x92', b'\x16', 0),
    (b'\xb2', b'\x15', 0),
    (b'\xff', b'\x00', 0),
    (b'\x11', b'\x00', 120),
    (b')', b'\x00', 100),
))


def custom_init(tft):
    """
    Send a bunch of custom commands to the display.
    Seems important for getting the colors to look right.
    """
    
    for cmd, bits, sleep_time in _NV3041A_INIT_CMDS:
        tft.send_cmd(
            cmd[0],
            bits[0],
            1 if bits else 0 # fully just guessing here,
            )
        time.sleep_ms(sleep_time)
    

def config():
    hspi = SPI(2, sck=Pin(47), mosi=None, miso=None, polarity=0, phase=0)
    panel = rm67162.QSPIPanel(
        spi=hspi,
        data=(Pin(21), Pin(48), Pin(40), Pin(39)),
        dc=Pin(7), # unused pin. Driver doesn't allow None
        cs=Pin(45),
        pclk=20_000_000,
        width=480,
        height=272,
#         width=480,
#         height=272,
    )
    tft = rm67162.RM67162(panel, bpp=16, color_space=rm67162.RGB)
    
    tft.reset()
    tft.init()
    custom_init(tft)
    
    tft.rotation(2)
    tft.invert_color(True)
    tft.mirror(True, False) # mirror on x axis. 
    
    return tft


def color565(r, g, b):
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | ((b & 0xF8) >> 3)
    return (c >> 8) | (c << 8)


# just for testing!
if __name__ == '__main__':
    import portal_main
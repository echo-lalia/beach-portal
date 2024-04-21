import rm67162
from machine import Pin, SPI

def config():
    hspi = SPI(2, sck=Pin(47), mosi=None, miso=None, polarity=0, phase=0)
    panel = rm67162.QSPIPanel(
        spi=hspi,
        data=(Pin(21), Pin(48), Pin(40), Pin(39)),
        dc=Pin(7),
        cs=Pin(45),
        pclk=30_000_000,
        width=480,
        height=272,
    )
    tft = rm67162.RM67162(panel, reset=Pin(7), bpp=16)
    
    tft.reset()
    tft.init()
    
    tft.rotation(1)
    tft.invert_color(True)
    return tft


def color565(r, g, b):
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | ((b & 0xF8) >> 3)
    return (c >> 8) | (c << 8)

# just for testing!
if __name__ == '__main__':
    import test
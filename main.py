from driver import epd2in13_V2
from machine import Pin
import time

clk = Pin(18)
mosi = Pin(23)
cs = Pin(5, Pin.OUT)
dc = Pin(17, Pin.OUT)
rst = Pin(16, Pin.OUT)
busy = Pin(4, Pin.IN)
landscape = False
black = 0
white = 1

epd = epd2in13_V2.EPD(cs, dc, rst, busy, clk, mosi, landscape)

epd.init(epd.FULL_UPDATE)

epd.fill(white)
epd.display()

epd.text('Full Update', 0, 0, black)
epd.display()

time.sleep(1)

epd.init(epd.PART_UPDATE)

epd.pixel(30, 10, black)
epd.displayPartial()
epd.hline(30, 30, 10, black)
epd.displayPartial()
epd.vline(30, 50, 10, black)
epd.displayPartial()
epd.line(30, 70, 40, 80, black)
epd.displayPartial()
epd.rect(30, 90, 10, 10, black)
epd.displayPartial()
epd.fill_rect(30, 110, 10, 10, black)
epd.displayPartial()
for row in range(1,30):
    epd.text(str(row),0,row*8,black)
    epd.displayPartial()



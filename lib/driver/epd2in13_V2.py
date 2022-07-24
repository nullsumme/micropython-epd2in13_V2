import framebuf
from machine import Pin, SPI
import time

class EPD(framebuf.FrameBuffer):

    FULL_UPDATE = 0
    PART_UPDATE = 1

    LUT_FULL_UPDATE= [
        0x80,0x60,0x40,0x00,0x00,0x00,0x00,             #LUT0: BB:     VS 0 ~7
        0x10,0x60,0x20,0x00,0x00,0x00,0x00,             #LUT1: BW:     VS 0 ~7
        0x80,0x60,0x40,0x00,0x00,0x00,0x00,             #LUT2: WB:     VS 0 ~7
        0x10,0x60,0x20,0x00,0x00,0x00,0x00,             #LUT3: WW:     VS 0 ~7
        0x00,0x00,0x00,0x00,0x00,0x00,0x00,             #LUT4: VCOM:   VS 0 ~7

        0x03,0x03,0x00,0x00,0x02,                       # TP0 A~D RP0
        0x09,0x09,0x00,0x00,0x02,                       # TP1 A~D RP1
        0x03,0x03,0x00,0x00,0x02,                       # TP2 A~D RP2
        0x00,0x00,0x00,0x00,0x00,                       # TP3 A~D RP3
        0x00,0x00,0x00,0x00,0x00,                       # TP4 A~D RP4
        0x00,0x00,0x00,0x00,0x00,                       # TP5 A~D RP5
        0x00,0x00,0x00,0x00,0x00,                       # TP6 A~D RP6
    ]

    LUT_PARTIAL_UPDATE = [ 
        0x00,0x00,0x00,0x00,0x00,0x00,0x00,             #LUT0: BB:     VS 0 ~7
        0x80,0x00,0x00,0x00,0x00,0x00,0x00,             #LUT1: BW:     VS 0 ~7
        0x40,0x00,0x00,0x00,0x00,0x00,0x00,             #LUT2: WB:     VS 0 ~7
        0x00,0x00,0x00,0x00,0x00,0x00,0x00,             #LUT3: WW:     VS 0 ~7
        0x00,0x00,0x00,0x00,0x00,0x00,0x00,             #LUT4: VCOM:   VS 0 ~7

        0x0A,0x00,0x00,0x00,0x00,                       # TP0 A~D RP0
        0x00,0x00,0x00,0x00,0x00,                       # TP1 A~D RP1
        0x00,0x00,0x00,0x00,0x00,                       # TP2 A~D RP2
        0x00,0x00,0x00,0x00,0x00,                       # TP3 A~D RP3
        0x00,0x00,0x00,0x00,0x00,                       # TP4 A~D RP4
        0x00,0x00,0x00,0x00,0x00,                       # TP5 A~D RP5
        0x00,0x00,0x00,0x00,0x00,                       # TP6 A~D RP6
    ]

    @staticmethod
    def rgb(r, g, b):
        return int((r > 127) or (g > 127) or (b > 127))

    def __init__(self, cs, dc, rst, busy, sck, mosi, landscape=False):
        self.mosi_pin = mosi
        self.sck_pin = sck
        self.cs_pin = cs  
        self.dc_pin = dc
        self.reset_pin = rst
        self.busy_pin = busy
        self.landscape = landscape
        self.width = 250 if landscape else 128
        self.height = 128 if landscape else 250
        self.buffer = bytearray(self.height * self.width // 8)
        self.mvb = memoryview(self.buffer)
        mode = framebuf.MONO_VLSB if landscape else framebuf.MONO_HLSB
        super().__init__(self.buffer, self.width, self.height, mode)

    def send_command(self, command, data=None):
        self.dc_pin(0)
        self.cs_pin(0)
        self.spi.write(bytes(c & 0xff for c in [command]))
        self.cs_pin(1)
        if data is not None:
            self.dc_pin(1)
            self.cs_pin(0)
            self.spi.write(data)
            self.cs_pin(1)

    def init(self, update_mode=FULL_UPDATE):      
        self.spi = SPI(1, 20000000,sck=Pin(18), mosi=Pin(23), miso=None)
        self.reset() # Hardware reset     
        if(update_mode == self.FULL_UPDATE):
            self.readBusy()
            self.send_command(0x12) # soft reset
            self.readBusy()
            self.send_command(0x74, bytes([0x54])) #set analog block control
            self.send_command(0x7E, bytes([0x3B])) #set digital block control
            self.send_command(0x01, bytes([0xF9, 0x00, 0x00])) #Driver output control
            self.send_command(0x11, bytes([0x03])) #data entry mode
            self.send_command(0x44, bytes([0x00, 0x0F])) #set Ram-X address start/end position
            self.send_command(0x45, bytes([0x00, 0x00, 0xF9, 0x00])) #set Ram-Y address start/end position        
            self.send_command(0x3C, bytes([0x03])) #BorderWavefrom
            self.send_command(0x2C, bytes([0x55]))     #VCOM Voltage
            self.send_command(0x32, bytes(self.LUT_FULL_UPDATE))
            self.send_command(0x4E, bytes([0x00]))   # set RAM x address count to 0
            self.send_command(0x4F, bytes([0x00, 0x00]))   # set RAM y address count to 0X127
            self.readBusy() 
        else:
            self.send_command(0x2C, bytes([0x26]))     #VCOM Voltage
            self.readBusy()
            self.send_command(0x32, bytes(self.LUT_PARTIAL_UPDATE))
            self.send_command(0x37, bytes([0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00]))
            self.send_command(0x22,bytes([0xC0]))
            self.send_command(0x20)
            self.readBusy()
            self.send_command(0x3C, bytes([0x01])) #BorderWavefrom
        return 0

    def display(self, buf1=bytearray(1)):
        buf1[0] = 0xff
        if self.landscape:
            print("not supported yet")
        else:
            self.send_command(0x24, bytes(self.mvb))
            self.turnOnDisplay()

    def displayPartial(self):
        if self.landscape:
            print("not supported yet")
        else:
            self.send_command(0x24, bytes(self.mvb))
            self.readBusy()   
            temp_buf = bytearray(len(self.mvb)) # inverted mvb
            for i, v in enumerate(self.mvb):
                temp_buf[i] = 0xFF & ~v
            self.send_command(0x26, bytes(temp_buf)) 
            self.readBusy()
            self.turnOnDisplayPartial()

    def turnOnDisplay(self):
        self.send_command(0x22, bytes([0xC7]))
        self.send_command(0x20)        
        self.readBusy()

    def turnOnDisplayPartial(self):
        self.send_command(0x22, bytes([0x0c]))
        self.send_command(0x20)    
        self.readBusy()

    def reset(self):
        self.reset_pin(1)
        time.sleep_ms(200) 
        self.reset_pin(0)
        time.sleep_ms(200) 
        self.reset_pin(1)
        time.sleep_ms(200)

    def readBusy(self):
        while(self.busy_pin() == 1):        
            time.sleep_ms(20)   

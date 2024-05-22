import time

import spidev
from RPi import GPIO

spi = spidev.SpiDev()
channel = 0
spi.open(0, 0)  # Use SPI bus 0, device 0
spi.max_speed_hz = 100000  # Set SPI clock speed to 500kHz
# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(13, GPIO.OUT)
GPIO.output(13, GPIO.HIGH)

time_limit = 60
start = time.time()
while start + time_limit > time.time():
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    print(adc)
    data = ((adc[1] & 3) << 8) + adc[2]
    voltage = data * 3.3 / 1023  # Convert the value to voltage (assuming 3.3V reference)
    print(f"Channel {channel} voltage: {voltage:.2f}V")

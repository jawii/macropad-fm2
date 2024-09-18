import time
import busio
import board
import adafruit_sht31d
import neopixel



print("\n\n============== Start ==============\n")

#
# Keyboard
#
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import time
import terminalio

kbd = Keyboard(usb_hid.devices)


print("\n\n============== Init Keyboard  ==============\n")
from digitalio import DigitalInOut
import adafruit_matrixkeypad
cols = [DigitalInOut(x) for x in (board.GP12, board.GP13, board.GP14, board.GP15)]  
rows = [DigitalInOut(x) for x in (board.GP2, board.GP3, board.GP4, board.GP5)]
keys = ((7, 8, 9, "x"),
        (4, 5, 6, "y"),
        (1, 2, 3, "z"),
        (0, '-', '#', 'D'))
#row1 = (Keycode.ONE, Keycode.TWO, Keycode.THREE)
#keys = ((1, 2, 3, 4),
#       (4, 5, 6))

keypad = adafruit_matrixkeypad.Matrix_Keypad(rows, cols, keys)
layout = {1: Keycode.ONE, 2: Keycode.TWO, 3: Keycode.THREE,
          4: Keycode.FOUR, 5: Keycode.FIVE, 6: Keycode.SIX, 
          7: Keycode.SEVEN, 8: Keycode.EIGHT, 9: Keycode.NINE,
          0: Keycode.ZERO, 'E': Keycode.ENTER}
    

# 
# Neopixel
#
print("\n\n============== Init Neopixel  ==============\n")
num_pixels = 8
pixels = neopixel.NeoPixel(board.GP17, num_pixels, pixel_order=neopixel.RGBW)

def wheel(pos):
    if pos < 85:
        return (int(pos * 3), int(255 - pos * 3), 0, 0)
    elif pos < 170:
        pos -= 85
        return (int(255 - pos * 3), 0, int(pos * 3), 0)
    else:
        pos -= 170
        return (0, int(pos * 3), int(255 - pos * 3), 0)

def rainbow_cycle(wait, step):
    color = wheel(step & 255) 
    for i in range(num_pixels):
        pixels[i] = color  
    pixels.show()
    time.sleep(wait)
    

#
# Init I2C
# 
print("\n\n============== Init I2C  ==============\n")
from digitalio import DigitalInOut, Direction
led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = False

# TODO 
# when using the serial monitor this throws sometimes 
# ValueError: GP1 in use 
# Restarting the board fixes the issue
while True:
    try:
        i2c = busio.I2C(scl=board.GP1, sda=board.GP0)
        break
    except ValueError as e:
        times = 50
        while times > 0:
            led.value = not led.value
            time.sleep(0.05)
            times -= 1

        print(f"Error initalizing the I2C: {e}")
        time.sleep(1)

led.value = True
print("I2C initialized")


#
# Display
#
print("\n\n============== Init Display  ==============\n")
import displayio
import adafruit_displayio_ssd1306
from adafruit_display_text import label
import pulseio

displayio.release_displays()
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=64, height=48)
display.rotation = 0

# Make the display context
splash = displayio.Group()
display.root_group = splash

# animation TODO:
"""
odb = displayio.OnDiskBitmap('/laptop.bmp')
face = displayio.TileGrid(odb, pixel_shader=odb.pixel_shader)
splash.append(face)
board.DISPLAY.refresh(target_frames_per_second=60)
for i in range(100):
    board.DISPLAY.brightness = 0.01 * i
    time.sleep(0.05)
while True:
    pass
"""

color_bitmap = displayio.Bitmap(64, 32, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)


inner_bitmap = displayio.Bitmap(62, 30, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  

inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=1, y=1)
splash.append(inner_sprite)

splash = displayio.Group()
display.root_group = splash

temp_text = label.Label(terminalio.FONT, text="0C", color=0xFFFFFF, x=10, y=10)
humidity_text = label.Label(terminalio.FONT, text="0%", color=0xFFFFFF, x=10, y=20)
keys_text = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=10, y=30)
splash.append(temp_text)
splash.append(humidity_text)
splash.append(keys_text)


#
# SHT31D
# 
print("\n\n============== Init SHT31D  ==============\n")
time.sleep(0.2)
sensor = adafruit_sht31d.SHT31D(i2c)



#
# Main loop
#
temp_update_interval = 1
last_update = time.monotonic()
step = 0  
last_keys = set()


while True:
    text = ""

    interval = time.monotonic() - last_update
    if time.monotonic() - last_update > temp_update_interval:
        temperature = sensor.temperature
        humidity = sensor.relative_humidity
        temp_text.text = f"{temperature:.1f} C"
        humidity_text.text = f"{humidity:.1f} %"
        last_update = time.monotonic()

    keys = set(keypad.pressed_keys)
    keystring = " ".join(str(k) for k in keys)
    keys_text.text = keystring
    new_keys = keys - last_keys
    if new_keys:
        for key in new_keys:
            if key in layout:
                kbd.press(layout[key])
                time.sleep(0.09)  
                kbd.release(layout[key])


    rainbow_cycle(0.0, step)
    step = (step + 1) % 256 

    time.sleep(0.01)



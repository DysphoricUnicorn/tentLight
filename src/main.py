from machine import Pin, ADC
from neopixel import NeoPixel
from lib.ubutton import uButton
import uasyncio

# -- Define constants

# Which GPIO pins are used to control the LEDs?
LED_DATA_PIN_NUMBER = 13
LED2_DATA_PIN_NUMBER = 8
LED1_COUNT = 32
LED2_COUNT = 30

# -- Setup device

# Set up the Neopixel library, which is an easy way to control the LEDs.
led_pin = Pin(LED_DATA_PIN_NUMBER, Pin.OUT)
led2_pin = Pin(LED2_DATA_PIN_NUMBER, Pin.OUT)
neopixel = NeoPixel(led_pin, LED1_COUNT)
neopixel2 = NeoPixel(led2_pin, LED2_COUNT)

# Set up ADC to control brightness
adc = ADC(Pin(2), atten=ADC.ATTN_11DB)

# Define an array of arrays of colors
color_combinations = [
    # Gummy Worm!
    [
        (247, 2, 2),
        (247, 47, 2),
        (247, 149, 2),
        (222, 247, 2),
        (59, 247, 2),
        (2, 247, 112),
        (2, 247, 231),
        (2, 108, 247),
        (2, 10, 247),
        (75, 2, 247),
        (149, 2, 247),
        (194, 2, 247),
        (247, 2, 223),
        (247, 2, 169),
        (247, 2, 116),
        (247, 2, 59),
    ],
    # Transgender pride flag
    [
        (255, 255, 255),
        (2, 186, 247),
        (247, 2, 239),
        (2, 186, 247),
    ],
    # Pansexual pride flag
    [
        (255, 2, 2),
        (243, 247, 2),
        (2, 80, 247),
    ],
    [
        (255, 255, 255)
    ]
]

mutable_state = {
    'color_index': 0,
    'animate': True,
    'animation_frames': [0, 0],
    'reverse': False,
    'tick': 0,
    'animation_slowdown': 2,
    'brightness_decimal': 0.1,
    'on': True,
    'last_color': (0, 0, 0),
}


def set_colors(pixels, frame_index):
    current_colors = [tuple(int(colorPart * mutable_state['brightness_decimal']) for colorPart in color)
                      for color in color_combinations[mutable_state['color_index']]]

    # Loop through all neopixels and set their colors
    color_index = 0
    if mutable_state['animate']:
        color_index = mutable_state['animation_frames'][frame_index]
        if mutable_state['reverse']:
            if mutable_state['animation_frames'][frame_index] < len(current_colors) - 1:
                mutable_state['animation_frames'][frame_index] += 1
            else:
                mutable_state['animation_frames'][frame_index] = 0
        else:
            if mutable_state['animation_frames'][frame_index] > 0:
                mutable_state['animation_frames'][frame_index] -= 1
            else:
                mutable_state['animation_frames'][frame_index] = len(current_colors) - 1

    for i in range(0, len(pixels)):
        # Ugly hack because one of the strips is broken, and we should really start packing soon rather than desoldering the board
        if frame_index == 0 and (
                current_colors[color_index][0] < 85 and current_colors[color_index][1] < 85 and current_colors[color_index][2] < 85):
            pixels[i] = (0, 0, 0)
        else:
            pixels[i] = current_colors[color_index]
        if current_colors[color_index] != mutable_state['last_color']:
            print(current_colors[color_index])
            mutable_state['last_color'] = current_colors[color_index]
        if color_index < len(current_colors) - 1:
            color_index += 1
        else:
            color_index = 0
    pixels.write()


def set_all_colors():
    for frame_index, pixels in enumerate([neopixel, neopixel2]):
        set_colors(pixels, frame_index)
        mutable_state['reverse'] = not mutable_state['reverse']


def change_color():
    print('change color')
    if mutable_state['color_index'] < len(color_combinations) - 1:
        mutable_state['color_index'] += 1
    else:
        mutable_state['color_index'] = 0
    mutable_state['animation_frames'] = [0, 0]
    set_all_colors()


def read_dial():
    current_val = adc.read_uv()
    new_brightness_decimal = current_val / 2875000
    if new_brightness_decimal < 0.06:
        new_brightness_decimal = 0
    brightness_diff = new_brightness_decimal - mutable_state['brightness_decimal']
    print(new_brightness_decimal)
    print(brightness_diff)
    if abs(brightness_diff) > 0.15:
        if brightness_diff > 0:
            print('up!')
            new_brightness_decimal = mutable_state['brightness_decimal'] + 0.1
        else:
            print('down!')
            new_brightness_decimal = mutable_state['brightness_decimal'] - 0.1
        mutable_state['brightness_decimal'] = new_brightness_decimal
    elif new_brightness_decimal == 0:
        print('no!')
        mutable_state['brightness_decimal'] = new_brightness_decimal


def toggle_animation():
    mutable_state['animate'] = not mutable_state['animate']


def toggle_on():
    if mutable_state['on']:
        mutable_state['on'] = False
        mutable_state['brightness_decimal'] = 0
    else:
        mutable_state['on'] = True
        read_dial()
    set_all_colors()


def toggle_animation_dir():
    mutable_state['reverse'] = not mutable_state['reverse']


async def main_loop():
    while True:
        if mutable_state['on']:
            set_all_colors()
            read_dial()
        await uasyncio.sleep_ms(50)


animate_button = uButton(
    Pin(6, Pin.IN, Pin.PULL_UP),
    cb_short=toggle_animation,
    cb_long=toggle_animation_dir,
    short_wait=True,
    act_low=True,
)

change_color_button = uButton(
    Pin(5, Pin.IN, Pin.PULL_UP),
    cb_short=change_color,
    cb_long=toggle_on,
    short_wait=True,
    act_low=True,
)

set_all_colors()

loop = uasyncio.get_event_loop()
loop.create_task(animate_button.run())
loop.create_task(change_color_button.run())
loop.create_task(main_loop())
loop.run_forever()

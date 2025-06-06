import sensor
import image
import time
import math
import pyb
from pyb import UART
from pyb import Pin
import omv
import rpc


def fits_thresold(color, thr):
    return (thr[0] <= color[0] <= thr[1] and
            thr[2] <= color[1] <= thr[3] and
            thr[4] <= color[2] <= thr[5])


def draw_line_from_angle(img, start, angle, color, length=100):
    x = start[0] + length * math.sin(math.radians(angle))
    y = start[1] - length * math.cos(math.radians(angle))
    img.draw_line(*start, int(x), int(y), color=color)


def goodAngle(ang):
    ang %= 360
    if ang > 180:
        ang = ang - 360
    return ang


def int_for_cpp(x):
    x = int(x)
    if x >= 0:
        return x
    return abs(x) + (1 << 15)


try:
    with open('thresholds.txt') as file:
        thresholds = file.read()
    thresholds = eval(thresholds)
except Exception:
    thresholds = [
        [0, 100, -127, 127, -127, 127],
        [0, 100, -127, 127, -127, 127],
        [0, 100, -127, 127, -127, 127],
    ]

# thresholds = [
#     (16, 85, -128, -23, -42, 54),  # green
#     (30, 45, -10, 20, -50, -15),  # blue
#     (50, 70, 0, 40, 20, 60),  # yellow
# ]

# green_thr = (16, 85, -128, -23, -42, 54)
yellow_thr = thresholds[0] #(50, 75, 0, 20, 30, 60)
blue_thr = thresholds[1] #(40, 55, -10, 15, -20, 5)
obst_thr = thresholds[2]
white_thr = thresholds[3]

SCREEN_CENTER = (160, 120)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)

#import setup_sensor

#print(dist_to_edge((160, 120), ((206, 240 - 49), (274, 240 - 20))))
#int('')

sensor.skip_frames(time = 2000)

import connect_to_kostyli
usb_vbus = Pin("USB_VBUS", Pin.IN, Pin.PULL_DOWN)
if(usb_vbus.value()):
    #pyb.LED(2).on()
    connect_to_kostyli.connect_to_comp()
    pass

#pyb.LED(3).on()

clock = time.clock()

ang = 0

uart = UART(3, 115200)

frame = 0

data = bytearray(38)

while True:
    clock.tick()
    img = sensor.snapshot()
#    img = img.median(2)

#    if frame % 200 == 0:
#        img.save(f"snapshot{time.time()}.bmp")
    frame += 1

#    img.draw_circle(*SCREEN_CENTER, 10, color=(255, 0, 0), fill=True)

    sectors = []

    blue = [360, 360, 360, (0, 0, 0), 360, 1000, 0, 0, 0]
    yellow = [360, 360, 360, (0, 0, 0), 360, 1000, 0, 0, 0]

    send_blue = [-1, -1, -1, -1, -1, -1, -1, -1]
    send_yellow = [-1, -1, -1, -1, -1, -1, -1, -1]

    blue_area = 0
    yellow_area = 0

    obst_angle = 360
    obst_dist = 1000

    for blob in img.find_blobs([blue_thr], pixels_threshold=50, area_threshold=50):
        if blob.roundness() > 0:
            print(blob.corners())

            if blob.area() > blue_area:
                img.draw_edges(blob.corners(), color=(0, 0, 255))
                send_blue = (2 * SCREEN_CENTER[0] - blob.corners()[0][0], 2 * SCREEN_CENTER[1] - blob.corners()[0][1],
                             2 * SCREEN_CENTER[0] - blob.corners()[1][0], 2 * SCREEN_CENTER[1] - blob.corners()[1][1],
                             2 * SCREEN_CENTER[0] - blob.corners()[2][0], 2 * SCREEN_CENTER[1] - blob.corners()[2][1],
                             2 * SCREEN_CENTER[0] - blob.corners()[3][0], 2 * SCREEN_CENTER[1] - blob.corners()[3][1])


    for blob in img.find_blobs([yellow_thr], pixels_threshold=50, area_threshold=50, merge=True):
        if blob.roundness() > 0:
            print(blob.corners())

            if blob.area() > yellow_area:
                img.draw_edges(blob.corners(), color=(255, 255, 0))
                send_yellow = (2 * SCREEN_CENTER[0] - blob.corners()[0][0], 2 * SCREEN_CENTER[1] - blob.corners()[0][1],
                               2 * SCREEN_CENTER[0] - blob.corners()[1][0], 2 * SCREEN_CENTER[1] - blob.corners()[1][1],
                               2 * SCREEN_CENTER[0] - blob.corners()[2][0], 2 * SCREEN_CENTER[1] - blob.corners()[2][1],
                               2 * SCREEN_CENTER[0] - blob.corners()[3][0], 2 * SCREEN_CENTER[1] - blob.corners()[3][1])

    for blob in img.find_blobs([obst_thr], pixels_threshold=100, area_threshold=100):
        if blob.roundness() > 0:
            img.draw_edges(blob.corners(), color=(0, 0, 0))

    if obst_angle != 360:
        draw_line_from_angle(img, SCREEN_CENTER, obst_angle, (200, 100, 60), obst_dist)

    send_yellow = list(map(int_for_cpp, send_yellow))
    send_blue = list(map(int_for_cpp, send_blue))

    print(send_yellow)

    data[0] = 255
    data[1] = 255
    data[2] = (send_yellow[0] >> 8) & 255
    data[3] = send_yellow[0] & 255
    data[4] = (send_yellow[1] >> 8) & 255
    data[5] = send_yellow[1] & 255
    data[6] = (send_yellow[2] >> 8) & 255
    data[7] = send_yellow[2] & 255
    data[8] = (send_yellow[3] >> 8) & 255
    data[9] = send_yellow[3] & 255
    data[10] = (send_yellow[4] >> 8) & 255
    data[11] = send_yellow[4] & 255
    data[12] = (send_yellow[5] >> 8) & 255
    data[13] = send_yellow[5] & 255
    data[14] = (send_yellow[6] >> 8) & 255
    data[15] = send_yellow[6] & 255
    data[16] = (send_yellow[7] >> 8) & 255
    data[17] = send_yellow[7] & 255

    data[18] = (send_blue[0] >> 8) & 255
    data[19] = send_blue[0] & 255
    data[20] = (send_blue[1] >> 8) & 255
    data[21] = send_blue[1] & 255
    data[22] = (send_blue[2] >> 8) & 255
    data[23] = send_blue[2] & 255
    data[24] = (send_blue[3] >> 8) & 255
    data[25] = send_blue[3] & 255
    data[26] = (send_blue[4] >> 8) & 255
    data[27] = send_blue[4] & 255
    data[28] = (send_blue[5] >> 8) & 255
    data[29] = send_blue[5] & 255
    data[30] = (send_blue[6] >> 8) & 255
    data[31] = send_blue[6] & 255
    data[32] = (send_blue[7] >> 8) & 255
    data[33] = send_blue[7] & 255

    obst_angle = int_for_cpp(obst_angle)
    obst_dist = int_for_cpp(obst_dist)
    data[34] = (obst_angle >> 8) & 255
    data[35] = obst_angle & 255
    data[36] = (obst_dist >> 8) & 255
    data[37] = obst_dist & 255
    uart.write(data)

    print(clock.fps())

import pyb
import sensor
import image
import time
import math
from pyb import UART
from pyb import Pin
import omv
import rpc

import connect_to_kostyli


#def connect_to_comp():
#    sensor.reset()
#    sensor.set_pixformat(sensor.RGB565)
#    sensor.set_framesize(sensor.QVGA)
#    sensor.skip_frames(time=2000)

#    omv.disable_fb(True)

#    interface = rpc.rpc_usb_vcp_slave()

#    def stream_generator_cb():
#        img = sensor.snapshot()
#        img.to_jpeg(quality=90)
#        try:
#            with open("thresholds.txt") as file:
#                thr = file.read()
#        except Exception:
#            thr = [[0, 100, -127, 127, -127, 127],
#                    [0, 100, -127, 127, -127, 127],
#                    [0, 100, -127, 127, -127, 127],
#                    [0, 100, -127, 127, -127, 127],
#                    [0, 100, -127, 127, -127, 127],]

#        thr_bt = bytearray(str(thr), 'utf8')
#        thr_bt += bytearray([0] * (200 - len(thr_bt)))

#        bt = thr_bt + img.bytearray()

#        return bt

#    def jpeg_image_stream_cb():
#        interface.stream_writer(stream_generator_cb)

#    def save_thresholds(thr):
#        with open("thresholds.txt", 'w') as file:
#            file.write(thr)
#        interface.schedule_callback(jpeg_image_stream_cb)
#        return bytes()

#    def jpeg_image_stream(data):
#        params = bytes(data).decode().split(";")
#        sensor.set_pixformat(eval(params[0]))
#        sensor.set_framesize(eval(params[1]))
#        interface.schedule_callback(jpeg_image_stream_cb)
#        return bytes()

#    JPEG_IMAGE_STREAM_CALLBACK = 48
#    SAVE_THRESHOLDS_CALLBACK = 96

#    interface.register_callback(jpeg_image_stream)
#    interface.register_callback(save_thresholds)

#    interface.loop()
#    pass


#usb_vbus = Pin("USB_VBUS", Pin.IN, Pin.PULL_DOWN)

#if(usb_vbus.value()):
##    pyb.LED(2).on()
#    connect_to_comp()

##pyb.LED(3).on()


def fits_thresold(color, thr):
    return (thr[0] <= color[0] <= thr[1] and
            thr[2] <= color[1] <= thr[3] and
            thr[4] <= color[2] <= thr[5])


def draw_line_from_angle(img, start, angle, color, length=100):
    x = start[0] + length * math.sin(math.radians(angle))
    y = start[1] - length * math.cos(math.radians(angle))
    img.draw_line(*start, int(x), int(y), color=color)


def dist_to_edge(point, edge):
    edge_len = (edge[0][0] - edge[1][0]) ** 2 + (edge[0][1] - edge[1][1]) ** 2
    p_dist1 = (edge[0][0] - point[0]) ** 2 + (edge[0][1] - point[1]) ** 2
    p_dist2 = (edge[1][0] - point[0]) ** 2 + (edge[1][1] - point[1]) ** 2

    if p_dist1 > edge_len + p_dist2:
        angle = math.degrees(math.atan2(edge[1][0] - point[0],
                                        edge[1][1] - point[1]))
        return (p_dist2 ** 0.5, angle)

    if p_dist2 > edge_len + p_dist1:
        angle = math.degrees(math.atan2(edge[0][0] - point[0],
                                        edge[0][1] - point[1]))
        return (p_dist1 ** 0.5, angle)

    a = edge[1][1] - edge[0][1]
    b = edge[0][0] - edge[1][0]
    c = edge[0][1] * edge[1][0] - edge[0][0] * edge[1][1]
    if a * a + b * b == 0:
        return (0, 0)
    eq = a * point[0] + b * point[1] + c
    dist = abs(eq) / ((a * a + b * b) ** 0.5)
    if eq > 0:
        angle = math.degrees(math.atan2(-a, -b))
    else:
        angle = math.degrees(math.atan2(a, b))
    return (dist, angle)


def goodAngle(ang):
    ang %= 360
    if ang > 180:
        ang = ang - 360
    return ang


def get_object_data(blob, color):
    x, y, width, height = blob.rect()
    lang = (x - 160) / 320 * 70
    rang = (x + width - 160) / 320 * 70
    cang = (lang + rang) / 2
    dist = y
    if y < 10:
        height = 140

    obj_data = [-lang, -cang, -rang, color, -cang, dist, width, height, blob.area()]

    return obj_data


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
#     (8, 64, 0, 100, -128, -19),  # blue
#     (19, 84, -45, 62, 18, 127),  # yellow
# ]

# green_thr = (16, 85, -128, -23, -42, 54)
yellow_thr = thresholds[0] #(60, 80, -10, 50, 30, 60)
blue_thr = thresholds[1] # (10, 45, -20, 10, -40, -5)

SCREEN_CENTER = (160, 120)

#print(dist_to_edge((160, 120), ((206, 240 - 49), (274, 240 - 20))))
#int('')

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)
#sensor.set_auto_gain(False)  # must be turned off for color tracking
#sensor.set_auto_whitebal(False)  # must be turned off for color tracking

#sensor.set_gainceiling(128)
#sensor.set_contrast(0)
#sensor.set_brightness(0)
#sensor.set_saturation(0)
#sensor.set_quality(100)
#sensor.set_auto_exposure(False, exposure_us=10000)

clock = time.clock()

ang = 0

uart = UART(3, 115200)

while True:
    clock.tick()
    img = sensor.snapshot()

    img.draw_circle(*SCREEN_CENTER, 10, color=(255, 0, 0), fill=True)

    sectors = []

    blue = [360, 360, 360, (0, 0, 0), 360, 1000, 0, 0, 0]
    yellow = [360, 360, 360, (0, 0, 0), 360, 1000, 0, 0, 0]

    send_blue = [360, 360, 360, 360, 1000, 0, 0]
    send_yellow = [360, 360, 360, 360, 1000, 0, 0]

    for blob in img.find_blobs([blue_thr], pixels_threshold=150, area_threshold=150):
        if blob.roundness() > 0:
            obj_data = get_object_data(blob, (0, 0, 255))

            if obj_data[8] > blue[8]:
                blue = obj_data
                send_blue = [blue[0], blue[1], blue[2], blue[4],
                             blue[5], blue[6], blue[7]]

            img.draw_edges(blob.corners())

    for blob in img.find_blobs([yellow_thr], pixels_threshold=150, area_threshold=150):
        if blob.roundness() > 0:
            obj_data = get_object_data(blob, (255, 255, 0))

            if obj_data[8] > yellow[8]:
                yellow = obj_data
                send_yellow = [yellow[0], yellow[1], yellow[2], yellow[4],
                               yellow[5], yellow[6], yellow[7]]

            img.draw_edges(blob.corners())

    send_yellow = list(map(int_for_cpp, send_yellow))
    send_blue = list(map(int_for_cpp, send_blue))

    # send_yellow = list(map(abs, send_yellow))
    # send_blue = list(map(abs, send_blue))

    #data = ' '.join(map(str, map(int, send_yellow + send_blue))) + ' '

    data = bytearray(30)

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

    data[16] = (send_blue[0] >> 8) & 255
    data[17] = send_blue[0] & 255
    data[18] = (send_blue[1] >> 8) & 255
    data[19] = send_blue[1] & 255
    data[20] = (send_blue[2] >> 8) & 255
    data[21] = send_blue[2] & 255
    data[22] = (send_blue[3] >> 8) & 255
    data[23] = send_blue[3] & 255
    data[24] = (send_blue[4] >> 8) & 255
    data[25] = send_blue[4] & 255
    data[26] = (send_blue[5] >> 8) & 255
    data[27] = send_blue[5] & 255
    data[28] = (send_blue[6] >> 8) & 255
    data[29] = send_blue[6] & 255

    print(data)
    #data = bytes(data)
    uart.write(data)

    # time.sleep(0.9)

    print(clock.fps())

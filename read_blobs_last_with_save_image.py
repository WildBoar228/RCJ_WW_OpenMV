import sensor
import image
import time
import math
from pyb import UART


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
    circle = blob.enclosing_circle()
    dist = ((circle[0] - SCREEN_CENTER[0]) ** 2 +
            (circle[1] - SCREEN_CENTER[1]) ** 2) ** 0.5
    cang = math.degrees(math.atan2(circle[0] - SCREEN_CENTER[0],
                                   SCREEN_CENTER[1] - circle[1]))
    cang = goodAngle(cang)
    delta = math.degrees(math.atan2(circle[2], dist))
    lang = goodAngle(cang - delta)
    rang = goodAngle(cang + delta)
    width = 2 * delta
    closAngle = cang
    corners = blob.corners()
    height = max(((corners[0][0] - corners[2][0]) ** 2 +
                  (corners[0][1] - corners[2][1]) ** 2) ** 0.5,
                 ((corners[1][0] - corners[3][0]) ** 2 +
                  (corners[1][1] - corners[3][1]) ** 2) ** 0.5)
    for i in range(len(corners)):
        dist2, ang2 = dist_to_edge(SCREEN_CENTER,
                                   ((corners[i][0], 2 * SCREEN_CENTER[1] - corners[i][1]),
                                    (corners[(i + 1) % 4][0],
                                     2 * SCREEN_CENTER[1] - corners[(i + 1) % 4][1])))
        if dist2 < dist:
            dist = dist2
            closAngle = ang2

    obj_data = [lang, cang, rang, color, closAngle, dist, width, height]

    return obj_data


thresholds = [
    (16, 85, -128, -23, -42, 54),  # green
    (30, 45, -10, 20, -50, -15),  # blue
    (50, 70, 0, 40, 20, 60),  # yellow
]

green_thr = (16, 85, -128, -23, -42, 54)
blue_thr = (25, 50, -15, 25, -55, -10)
yellow_thr = (30, 55, -10, 40, 20, 60)

SCREEN_CENTER = (160, 120)

#print(dist_to_edge((160, 120), ((206, 240 - 49), (274, 240 - 20))))
#int('')

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)  # must be turned off for color tracking
sensor.set_auto_whitebal(False)  # must be turned off for color tracking

sensor.set_gainceiling(128)
sensor.set_contrast(0)
sensor.set_brightness(0)
sensor.set_saturation(0)
sensor.set_quality(100)
sensor.set_auto_exposure(False, exposure_us=5000)
clock = time.clock()

ang = 0

uart = UART(3, 115200)

frame_index = 0

while True:
    frame_index += 1
    clock.tick()
    img = sensor.snapshot()

    if frame_index % (200) == 0:
        img.save(f"snapshot{frame_index}.bmp")

        img.draw_circle(*SCREEN_CENTER, 10, color=(255, 0, 0), fill=True)

    sectors = []

    blue = [360, 360, 360, (0, 0, 0), 360, 100, 0, 0]
    yellow = [360, 360, 360, (0, 0, 0), 360, 100, 0, 0]

    send_blue = [360, 360, 360, 360, 100, 0, 0]
    send_yellow = [360, 360, 360, 360, 100, 0, 0]

    for blob in img.find_blobs([blue_thr], pixels_threshold=50, area_threshold=50):
        if blob.roundness() > 0:
            obj_data = get_object_data(blob, (0, 0, 255))

            if obj_data[6] > blue[6] and obj_data[5] < 110:
                blue = obj_data
                send_blue = [blue[0], blue[1], blue[2], blue[4],
                             blue[5], blue[6], blue[7]]

            img.draw_edges(blob.corners())

    for blob in img.find_blobs([yellow_thr], pixels_threshold=50, area_threshold=50):
        if blob.roundness() > 0:
            obj_data = get_object_data(blob, (255, 255, 0))

            if obj_data[6] > yellow[6] and obj_data[5] < 110:
                yellow = obj_data
                send_yellow = [yellow[0], yellow[1], yellow[2], yellow[4],
                               yellow[5], yellow[6], yellow[7]]

            img.draw_edges(blob.corners())

    sectors = [blue, yellow]
    #print(sectors)
    #draw_line_from_angle(img, SCREEN_CENTER, ang, (255, 0, 0))
    for s in sectors:
        draw_line_from_angle(img, SCREEN_CENTER, s[0], s[3])
        draw_line_from_angle(img, SCREEN_CENTER, s[2], s[3])
        draw_line_from_angle(img, SCREEN_CENTER, s[1], (255, 0, 0))
        draw_line_from_angle(img, SCREEN_CENTER, s[4], (0, 0, 0), s[5])
    ang += 5

    data = ' '.join(map(str, map(int, send_yellow + send_blue))) + ' '
    print(data)
    uart.write(data)

    print(clock.fps())

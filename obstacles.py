import sensor
import image
import time
import math
from pyb import UART


def draw_line_from_angle(img, start, angle, color, length=100, thick=1):
    x = start[0] + length * math.sin(math.radians(angle))
    y = start[1] - length * math.cos(math.radians(angle))
    img.draw_line(*start, int(x), int(y), color=color, thickness=thick)


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
    for i in range(len(corners)):
        dist2, ang2 = dist_to_edge(SCREEN_CENTER,
                                   ((corners[i][0], 2 * SCREEN_CENTER[1] - corners[i][1]),
                                    (corners[(i + 1) % 4][0],
                                     2 * SCREEN_CENTER[1] - corners[(i + 1) % 4][1])))
        if dist2 < dist:
            dist = dist2
            closAngle = ang2

#    corners = blob.min_corners()
#    for i in range(len(corners)):
#        dist2, ang2 = dist_to_edge(SCREEN_CENTER,
#                                   ((corners[i][0], 2 * SCREEN_CENTER[1] - corners[i][1]),
#                                    (corners[(i + 1) % 4][0],
#                                     2 * SCREEN_CENTER[1] - corners[(i + 1) % 4][1])))
#        if dist2 < dist:
#            dist = dist2
#            closAngle = ang2

    obj_data = [lang, cang, rang, color, closAngle, dist, width]

    return obj_data


green_thr = (0, 20, -10, 10, -10, 10)
SCREEN_CENTER = (160, 120)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)

clock = time.clock()

while(True):
    clock.tick()
    img = sensor.snapshot()

    closest = [360, 10000]

#    for angle in range(0, 360, 30):
#        draw_line_from_angle(img, SCREEN_CENTER, angle, (150, 150, 150), 200, 3)

    for blob in img.find_blobs([green_thr], pixels_threshold=200, area_threshold=200,
                               invert=False):
        if blob.roundness() > 0:
            img.draw_edges(blob.corners(), color=(0, 255, 0))
#            img.draw_edges(blob.min_corners(), color=(255, 0, 0))

            obj_data = get_object_data(blob, (0, 0, 0))

            if obj_data[5] < closest[1]:
                closest = (obj_data[4], obj_data[5])

    print(closest)
    draw_line_from_angle(img, SCREEN_CENTER, closest[0], (0, 0, 0), closest[1])

    print(clock.fps())

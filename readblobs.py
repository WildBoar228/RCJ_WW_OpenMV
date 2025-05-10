import sensor
import image
import time
import math


def fits_thresold(color, thr):
    return (thr[0] <= color[0] <= thr[1] and
            thr[2] <= color[1] <= thr[3] and
            thr[4] <= color[2] <= thr[5])


def draw_line_from_angle(img, start, angle, color, length=100):
    x = start[0] + length * math.sin(math.radians(angle))
    y = start[1] - length * math.cos(math.radians(angle))
    img.draw_line(*start, int(x), int(y), color=color)


thresholds = [
    (16, 85, -128, -23, -42, 54),  # green
    (8, 64, 10, 100, -128, -19),  # blue
    (19, 84, -45, 62, 18, 127),  # yellow
]

green_thr = (16, 85, -128, -23, -42, 54)
blue_thr = (8, 64, 10, 100, -128, -19)
yellow_thr = (19, 84, -45, 62, 18, 127)

SCREEN_CENTER = (160, 120)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)  # must be turned off for color tracking
sensor.set_auto_whitebal(False)  # must be turned off for color tracking
clock = time.clock()

ang = 0

while True:
    clock.tick()
    img = sensor.snapshot()

    img.draw_circle(*SCREEN_CENTER, 10, color=(255, 0, 0), fill=True)

    sectors = []

    for blob in img.find_blobs(thresholds, pixels_threshold=200, area_threshold=200):
        if blob.roundness() > 0.3:
            color = (255, 255, 255)
            pix = image.rgb_to_lab(img.get_pixel(blob.cx(), blob.cy()))

            if fits_thresold(pix, thresholds[0]):
                color = (0, 255, 0)
            elif fits_thresold(pix, thresholds[1]):
                color = (0, 0, 255)
            elif fits_thresold(pix, thresholds[2]):
                color = (255, 255, 0)
            else:
                continue

            circle = blob.enclosing_circle()
            dist = ((circle[0] - SCREEN_CENTER[0]) ** 2 +
                    (circle[1] - SCREEN_CENTER[1]) ** 2) ** 0.5
            cang = math.degrees(math.atan2(circle[0] - SCREEN_CENTER[0],
                                           SCREEN_CENTER[1] - circle[1]))
            delta = math.degrees(math.atan2(circle[2], dist))
            lang = cang - delta
            rang = cang + delta
            #print(f'{lang} .. {cang} .. {rang},   {color}')
            #img.draw_circle(circle, color=color)

            sectors.append((lang, cang, rang, color))

    sectors.sort()
    print(sectors)
    #draw_line_from_angle(img, SCREEN_CENTER, ang, (255, 0, 0))
    for s in sectors:
        draw_line_from_angle(img, SCREEN_CENTER, s[0], s[3])
        draw_line_from_angle(img, SCREEN_CENTER, s[2], s[3])
        draw_line_from_angle(img, SCREEN_CENTER, s[1], (255, 0, 0))
    ang += 5

    print(clock.fps())

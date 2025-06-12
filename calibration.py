# Untitled - By: Игорь - Sun Sep 8 2024

import sensor, image, time, math

def circle_mask(x, y, r):
    img.draw_rectangle(0, 0, x - r, 240, fill=True, color=(0, 0, 0))
    img.draw_rectangle(x + r, 0, 320 - (x + r), 240, fill=True, color=(0, 0, 0))
    img.draw_rectangle(0, 0, 320, y - r, fill=True, color=(0, 0, 0))
    img.draw_rectangle(0, y + r, 320, 240 - (y + r), fill=True, color=(0, 0, 0))

    pos_x = int(x + math.sin(math.degrees(45)) * r * 1.41)
    pos_y = int(y + math.cos(math.degrees(45)) * r * 1.41)

    for angle in range(45, 360, 90):
        pos_x = int(x + math.sin(math.radians(angle)) * r * 1.41)
        pos_y = int(y + math.cos(math.radians(angle)) * r * 1.41)
        # print(pos_x, pos_y)
        img.draw_circle(pos_x, pos_y, int(r * 0.41), color=(0, 0, 0), fill=True)

    pass

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
#sensor.set_auto_gain(False)  # must be turned off for color tracking
#sensor.set_auto_whitebal(False)  # must be turned off for color tracking

#sensor.set_gainceiling(128)
#sensor.set_contrast(0)
#sensor.set_brightness(0)
#sensor.set_saturation(0)
#sensor.set_quality(100)
#sensor.set_auto_exposure(False, exposure_us=15000)
sensor.skip_frames(time = 2000)

clock = time.clock()

# try:
#     with open('thresholds.txt') as file:
#         thresholds = file.read()
#     thresholds = eval(thresholds)
# except FileNotFoundError:
thresholds = [
         [0, 10, -5, 5, -5, 5]
     ]

#print(thresholds)

print(dir(image))
#mirror_mask = image.mask_circle(160, 120, 100)

while(True):
    clock.tick()
    img = sensor.snapshot()
    img.draw_line(160, 120, 160+120, 240)
    img.draw_line(160, 120, 40, 240)
    img.draw_line(160, 120, 160+120, 0)
    img.draw_line(160, 120, 40, 0)
    img.draw_circle(160, 120, 2, color=(255, 0, 0), fill=True)
    # img.draw_rectangle(0, 0, 38, 240, color=(0, 0, 0), fill=True)
    circle_mask(164, 121, 122)
    # img_bitmap = img.binary([thresholds[0]])
    #img = img.b_and(img, mask=mirror_mask)
    print(clock.fps())

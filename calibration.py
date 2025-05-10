# Untitled - By: Игорь - Sun Sep 8 2024

import sensor, image, time

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

while(True):
    clock.tick()
    img = sensor.snapshot()
    img.draw_line(160, 120, 160+120, 240)
    img.draw_line(160, 120, 40, 240)
    img.draw_line(160, 120, 160+120, 0)
    img.draw_line(160, 120, 40, 0)
    img.draw_circle(160, 120, 2, color=(255, 0, 0), fill=True)
#    img_bitmap = img.binary([thresholds[0]])
    print(clock.fps())

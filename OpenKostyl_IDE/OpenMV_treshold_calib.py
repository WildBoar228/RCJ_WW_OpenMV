# Image Transfer - As The Controller Device
#
# This script is meant to talk to the "image_transfer_jpg_streaming_as_the_remote_device_for_your_computer.py" on the OpenMV Cam.
#
# This script shows off how to transfer the frame buffer to your computer as a jpeg image.

import io, pygame, rpc, serial, serial.tools.list_ports, socket, sys, time
from PIL import Image
import numpy as np
from skimage.color import rgb2lab
from widgets import *

# Fix Python 2.x.
try: input = raw_input
except NameError: pass

# The RPC library above is installed on your OpenMV Cam and provides multiple classes for
# allowing your OpenMV Cam to control over USB or WIFI.

##############################################################
# Choose the interface you wish to control an OpenMV Cam over.
##############################################################

# Uncomment the below lines to setup your OpenMV Cam for controlling over a USB VCP.
#
# * port - Serial Port Name.
#

port_name = ""

print("\nAvailable Ports:\n")
for port, desc, hwid in serial.tools.list_ports.comports():
    print("{} : {} [{}]".format(port, desc, hwid))
    if "openmv" in desc.lower():
        port_name = port

sys.stdout.write("\nPlease enter a port name: ")
print(port_name)
sys.stdout.flush()

interface = rpc.rpc_usb_vcp_master(port_name) #input())
print("")
sys.stdout.flush()

# Uncomment the below line to setup your OpenMV Cam for controlling over WiFi.
#
# * slave_ip - IP address to connect to.
# * my_ip - IP address to bind to ("" to bind to all interfaces...)
# * port - Port to route traffic to.
#
# interface = rpc.rpc_network_master(slave_ip="xxx.xxx.xxx.xxx", my_ip="", port=0x1DBA)

##############################################################
# Call Back Handlers
##############################################################


def threshold_filter(thr, pixels):
    labpix = rgb2lab(pixels / 255)
    ind = np.all(labpix >= thr[::2], axis=2) * np.all(labpix <= thr[1::2], axis=2)
    return ind * 255


def filter_L(thr, pixels):
    labpix = rgb2lab(pixels / 255)
    ind_low = labpix[:,:,0] < thr[0]
    ind_high = labpix[:,:,0] > thr[1]
    ind_ok = (labpix[:,:,0] >= thr[0]) * (labpix[:,:,0] <= thr[1])
    labpix[ind_low] = np.array([0, 0, 0])
    labpix[ind_ok] = np.array([255, 255, 255])
    labpix[ind_high] = np.array([100, 100, 100])
    return labpix


def filter_A(thr, pixels):
    labpix = rgb2lab(pixels / 255)
    ind_low = labpix[:,:,1] < thr[2]
    ind_high = labpix[:,:,1] > thr[3]
    ind_ok = (labpix[:,:,1] >= thr[2]) * (labpix[:,:,1] <= thr[3])
    labpix[ind_low] = np.array([0, 100, 0])
    labpix[ind_ok] = np.array([255, 255, 255])
    labpix[ind_high] = np.array([100, 0, 0])
    return labpix


def filter_B(thr, pixels):
    labpix = rgb2lab(pixels / 255)
    ind_low = labpix[:,:,2] < thr[4]
    ind_high = labpix[:,:,2] > thr[5]
    ind_ok = (labpix[:,:,2] >= thr[4]) * (labpix[:,:,1] <= thr[5])
    labpix[ind_low] = np.array([0, 0, 100])
    labpix[ind_ok] = np.array([255, 255, 255])
    labpix[ind_high] = np.array([80, 80, 0])
    return labpix


def threshold_from_area(rect, pixels):
    labpix = rgb2lab(pixels / 255)
    print(rect.left, rect.right, '     ', labpix.shape)
    print(rect.top, rect.bottom, '     ', rect.height)
    print(np.min(labpix[rect.left : rect.right + 1, rect.top : rect.bottom + 1, 0]),
          np.max(labpix[rect.left : rect.right + 1, rect.top : rect.bottom + 1, 0]))
    thr = np.array([np.min(labpix[rect.left : rect.right + 1, rect.top : rect.bottom + 1, 0]),
                    np.max(labpix[rect.left : rect.right + 1, rect.top : rect.bottom + 1, 0]),
                    np.min(labpix[rect.left : rect.right + 1, rect.top : rect.bottom + 1, 1]),
                    np.max(labpix[rect.left : rect.right + 1, rect.top : rect.bottom + 1, 1]),
                    np.min(labpix[rect.left : rect.right + 1, rect.top : rect.bottom + 1, 2]),
                    np.max(labpix[rect.left : rect.right + 1, rect.top : rect.bottom + 1, 2]),
                    ]).astype(np.int8)
    return thr


def threshold_sum(thr1, thr2):
    thr = np.array(thr1)
    thr[0] = min(thr1[0], thr2[0])
    thr[1] = max(thr1[1], thr2[1])
    thr[2] = min(thr1[2], thr2[2])
    thr[3] = max(thr1[3], thr2[3])
    thr[4] = min(thr1[4], thr2[4])
    thr[5] = max(thr1[5], thr2[5])
    return thr

def threshold_diff(thr1, thr2):
    thr = np.array(thr1)
    
    # if thr2[0] > thr[0] or thr2[1] < thr[1]:
    #     if (thr2[0] <= thr[0] and thr2[1] >= thr[0]):
    #         thr[0] = thr2[1]
    #     if (thr2[1] >= thr[1] and thr2[0] <= thr[1]):
    #         thr[1] = thr2[0]

    # if thr2[2] > thr[2] or thr2[3] < thr[3]:
    #     if (thr2[2] <= thr[2] and thr2[3] >= thr[2]):
    #         thr[2] = thr2[3]
    #     if (thr2[1] >= thr[3] and thr2[2] <= thr[3]):
    #         thr[3] = thr2[2]

    # if thr2[4] > thr[4] or thr2[5] < thr[5]:
    #     if (thr2[4] <= thr[4] and thr2[5] >= thr[4]):
    #         thr[4] = thr2[3]
    #     if (thr2[1] >= thr[5] and thr2[4] <= thr[5]):
    #         thr[5] = thr2[4]
        
    # print(thr1, '-', thr2, '=', thr)
        
    return thr


def save_to_cam():
    global save_thr
    save_thr = True


def set_thr_to_sliders():
    global thresholds
    global thr_index

    widgets['slider_L_low'].set_value(thresholds[thr_index][0])
    widgets['slider_L_high'].set_value(thresholds[thr_index][1])

    widgets['slider_A_low'].set_value(thresholds[thr_index][2])
    widgets['slider_A_high'].set_value(thresholds[thr_index][3])

    widgets['slider_B_low'].set_value(thresholds[thr_index][4])
    widgets['slider_B_high'].set_value(thresholds[thr_index][5])


def set_pause():
    global is_pause
    if is_pause:
        is_pause = False
        widgets['btn_pause'].label.text = '||'
    else:
        is_pause = True
        widgets['btn_pause'].label.text = '>'


pygame.init()
screen_w = 1280
screen_h = 600
# try:
    #screen = pygame.display.set_mode((screen_w, screen_h), flags=pygame.RESIZABLE)
# except TypeError:
screen = pygame.display.set_mode((screen_w, screen_h))

pygame.display.set_caption("Frame Buffer")
clock = pygame.time.Clock()

take_thr_from_cam = True
save_thr = False
thresholds = [
    [15, 45, -15, 25, -45, -10],
    [0, 100, -127, 127, -127, 127],
    [0, 100, -127, 127, -127, 127],
    [0, 100, -127, 127, -127, 127],
    [0, 100, -127, 127, -127, 127],
]

thr_buffer = [-1, -1, -1, -1, -1, -1]

thr_index = 0
edit_index = 0

pixels = np.array([])
pixels_processed = np.array([])
process_mode = 'Bitmap'
is_pause = False


def set_proc_mode(mode):
    global process_mode
    process_mode = mode


widgets = {'img_src': ImageNumpy(screen, pygame.Rect(20, 60, 320, 240), source=pixels, select_area=True),
           'img_proc': ImageNumpy(screen, pygame.Rect(20 + 320 + 20, 60, 320, 240), source=pixels_processed),

           'btn_bitmap': Button(screen, pygame.Rect(20 + 320 + 20, 10, 100, 40),
                                label=Label(screen, pygame.Rect(20 + 320 + 20, 10, 100, 40),
                                            text='Bitmap', color=(255, 255, 255),
                                            font=pygame.font.Font(None, 40),
                                            stratch=True),
                                func=set_proc_mode, args=('Bitmap',),
                                colors={'normal': (0, 0, 0),
                                        'pressed': (100, 100, 100)}),

           'btn_l': Button(screen, pygame.Rect(360 + 100 + 10, 10, 40, 40),
                                label=Label(screen, pygame.Rect(360 + 100 + 10, 10, 40, 40),
                                            text='L', color=(255, 255, 255),
                                            font=pygame.font.Font(None, 40),
                                            stratch=True),
                                func=set_proc_mode, args=('L',),
                                colors={'normal': (0, 0, 0),
                                        'pressed': (100, 100, 100)}),

           'btn_a': Button(screen, pygame.Rect(470 + 40 + 10, 10, 40, 40),
                                label=Label(screen, pygame.Rect(470 + 40 + 10, 10, 40, 40),
                                            text='A', color=(255, 255, 255),
                                            font=pygame.font.Font(None, 40),
                                            stratch=True),
                                func=set_proc_mode, args=('A',),
                                colors={'normal': (0, 0, 0),
                                        'pressed': (100, 100, 100)}),

           'btn_b': Button(screen, pygame.Rect(520 + 40 + 10, 10, 40, 40),
                                label=Label(screen, pygame.Rect(520 + 40 + 10, 10, 40, 40),
                                            text='B', color=(255, 255, 255),
                                            font=pygame.font.Font(None, 40),
                                            stratch=True),
                                func=set_proc_mode, args=('B',),
                                colors={'normal': (0, 0, 0),
                                        'pressed': (100, 100, 100)}),

            'label_mode': Label(screen, pygame.Rect(20 + 320 + 20, 60 + 240 + 20, 0, 0),
                                'Mode', color=(0, 0, 0), stratch=False),

            'label_coords': Label(screen, pygame.Rect(20, 60 + 240 + 20, 0, 0),
                                'Coords', color=(0, 0, 0), stratch=False,
                                font=pygame.font.Font(None, 20)),
            
            'slider_L_low': HorizSlider(screen, pygame.Rect(20, 360, 10, 10),
                                    borders=(20, 400), values=(0, 100),
                                    radius=8, bg_width=3,
                                    color=(0, 0, 0)),
            'slider_L_high': HorizSlider(screen, pygame.Rect(20, 370, 10, 10),
                                    borders=(20, 400), values=(0, 100),
                                    radius=8, bg_width=3,
                                    color=(150, 150, 150)),
            'label_L': Label(screen, pygame.Rect(420, 370, 0, 0),
                            'L  [0, 100]', color=(0, 0, 0), stratch=False,
                            font=pygame.font.Font(None, 30)),
            
            'slider_A_low': HorizSlider(screen, pygame.Rect(20, 400, 10, 10),
                                    borders=(20, 400), values=(-127, 127),
                                    radius=8, bg_width=3,
                                    color=(100, 150, 100)),
            'slider_A_high': HorizSlider(screen, pygame.Rect(20, 410, 10, 10),
                                    borders=(20, 400), values=(-127, 127),
                                    radius=8, bg_width=3,
                                    color=(150, 100, 100)),
            'label_A': Label(screen, pygame.Rect(420, 400, 0, 0),
                            'A  [-127, 127]', color=(0, 0, 0), stratch=False,
                            font=pygame.font.Font(None, 30)),
            
            'slider_B_low': HorizSlider(screen, pygame.Rect(20, 450, 10, 10),
                                    borders=(20, 400), values=(-127, 127),
                                    radius=8, bg_width=3,
                                    color=(100, 100, 150)),
            'slider_B_high': HorizSlider(screen, pygame.Rect(20, 460, 10, 10),
                                    borders=(20, 400), values=(-127, 127),
                                    radius=8, bg_width=3,
                                    color=(150, 150, 80)),
            'label_B': Label(screen, pygame.Rect(420, 450, 0, 0),
                            'B  [-127, 127]', color=(0, 0, 0), stratch=False,
                            font=pygame.font.Font(None, 30)),

            'itemlist_thr': ItemList(screen, pygame.Rect(750, 20, 0, 0),
                                     items=[Label(screen, pygame.Rect(750, 20, 300, 60),
                                            'Thr 1: ', color=(0, 0, 0), stratch=True,
                                            font=pygame.font.Font(None, 25)),
                                            
                                            Label(screen, pygame.Rect(750, 20, 300, 60),
                                            'Thr 2: ', color=(0, 0, 0), stratch=True,
                                            font=pygame.font.Font(None, 25)),
                                            
                                            Label(screen, pygame.Rect(750, 20, 300, 60),
                                            'Thr 3: ', color=(0, 0, 0), stratch=True,
                                            font=pygame.font.Font(None, 25)),
                                            
                                            Label(screen, pygame.Rect(750, 20, 300, 60),
                                            'Thr 4: ', color=(0, 0, 0), stratch=True,
                                            font=pygame.font.Font(None, 25)),
                                            
                                            Label(screen, pygame.Rect(750, 20, 300, 60),
                                            'Thr 5: ', color=(0, 0, 0), stratch=True,
                                            font=pygame.font.Font(None, 25)),],

                                     padding_y=30),
            
            'itemlist_select': ItemList(screen, pygame.Rect(20, 10, 40, 40),
                                     items=[Label(screen, pygame.Rect(20, 10, 40, 40),
                                            'R', color=(0, 0, 0), stratch=True,
                                            font=pygame.font.Font(None, 25)),
                                         
                                            Label(screen, pygame.Rect(20, 10, 40, 40),
                                            '+', color=(0, 0, 0), stratch=True,
                                            font=pygame.font.Font(None, 25)),
                                            
                                            Label(screen, pygame.Rect(20, 10, 40, 40),
                                            '-', color=(0, 0, 0), stratch=True,
                                            font=pygame.font.Font(None, 25)),
                                     ],

                                     padding_x=60),

           'btn_save': Button(screen, pygame.Rect(800, 400, 150, 40),
                              label=Label(screen, pygame.Rect(800, 400, 150, 40),
                                            text='Save', color=(255, 255, 255),
                                            font=pygame.font.Font(None, 40),
                                            stratch=True),
                                func=save_to_cam,
                                colors={'normal': (0, 0, 0),
                                        'pressed': (100, 100, 100)}),
            
            'btn_pause': Button(screen, pygame.Rect(300, 10, 40, 40),
                                label=Label(screen, pygame.Rect(300, 10, 40, 40),
                                            text='||', color=(255, 255, 255),
                                            font=pygame.font.Font(None, 40),
                                            stratch=True),
                                func=set_pause,
                                colors={'normal': (0, 0, 0),
                                        'pressed': (100, 100, 100)}),
}
wnames = list(widgets.keys())

keys = {}
press_pos = (-1, -1)

widgets['slider_L_low'].set_value(0)
widgets['slider_L_high'].set_value(100)

widgets['slider_A_low'].set_value(-127)
widgets['slider_A_high'].set_value(127)

widgets['slider_B_low'].set_value(-127)
widgets['slider_B_high'].set_value(127)


# This will be called with the bytes() object generated by the slave device.
def jpg_frame_buffer_cb(data):
    global edit_index
    global process_mode
    global thresholds
    global thr_index
    global thr_buffer
    global save_thr
    global take_thr_from_cam

    sys.stdout.flush()

    pygame.draw.rect(screen, (200, 200, 200),
                     (0, 0, screen_w, screen_h))
    
    cam_thr = str(data[:300])
    #print(cam_thr, len(cam_thr))
    if take_thr_from_cam:
        take_thr_from_cam = False
        cam_thr = cam_thr[cam_thr.find('['):cam_thr.rfind(']') + 1]
        thresholds = eval(cam_thr)
        set_thr_to_sliders()

    data = data[300:]
    #print(cam_thr, len(cam_thr))
    print(len(cam_thr))

    try:
        image = Image.open(io.BytesIO(data))
    except Exception as exc:
        print(exc)
        return

    try:
        if not is_pause:
            widgets['img_src'].pixels = np.rot90(np.array(image), k=3)
    except Exception: return

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
            
        if event.type == pygame.KEYDOWN:
            keys[event.key] = 1
            # if event.key == pygame.K_a:
            #     edit_index -= 1
                    
            # if event.key == pygame.K_d:
            #     edit_index += 1
            
            if event.key == pygame.K_c and (keys.get(pygame.K_LCTRL) or keys.get(pygame.K_RCTRL)):
                thr_buffer = thresholds[thr_index].copy()

            if event.key == pygame.K_v and (keys.get(pygame.K_LCTRL) or keys.get(pygame.K_RCTRL)):
                if thr_buffer[0] != -1:
                    thresholds[thr_index] = thr_buffer.copy()
                    set_thr_to_sliders()
        
        if event.type == pygame.KEYUP:
            keys[event.key] = 0
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            for w in wnames[::-1]:
                if widgets[w].process_mousedown(event):
                    break

            if thr_index != widgets['itemlist_thr'].chosen:
                thr_index = widgets['itemlist_thr'].chosen
                set_thr_to_sliders()

        if event.type == pygame.MOUSEBUTTONUP:
            flag = widgets['img_src'].first_press is not None
            for w in wnames[::-1]:
                widgets[w].process_mouseup(event)
            
            if flag and widgets['img_src'].selected_area is not None:
                rect = widgets['img_src'].selected_area.copy()

                rect.left -= widgets['img_src'].rect.left
                rect.top -= widgets['img_src'].rect.top
                rect.width //= 2
                rect.height //= 2
                rect.left //= 2
                rect.top //= 2

                if widgets['itemlist_select'].chosen == 0:
                    thresholds[thr_index] = threshold_from_area(rect, widgets['img_src'].pixels).copy()
                    with open('color_data.txt', 'w') as file:
                        line = ' '.join(map(str, list(thresholds[thr_index])))
                        file.write(line + ' 1\n')

                if widgets['itemlist_select'].chosen == 1:
                    thresholds[thr_index] = threshold_sum(thresholds[thr_index],
                                                          threshold_from_area(rect, widgets['img_src'].pixels).copy())
                    with open('color_data.txt', 'a') as file:
                        line = ' '.join(map(str, list(thresholds[thr_index])))
                        file.write(line + ' 1\n')
                    
                if widgets['itemlist_select'].chosen == 2:
                    thresholds[thr_index] = threshold_diff(thresholds[thr_index],
                                                          threshold_from_area(rect, widgets['img_src'].pixels).copy())
                    with open('color_data.txt', 'a') as file:
                        line = ' '.join(map(str, list(thresholds[thr_index])))
                        file.write(line + ' 0\n')
                thresholds[thr_index] = list(thresholds[thr_index])

                set_thr_to_sliders()

        if event.type == pygame.MOUSEMOTION:
            for w in wnames[::-1]:
                widgets[w].process_mousemotion(event)

    if process_mode == 'Bitmap':
        widgets['img_proc'].pixels = threshold_filter(thresholds[thr_index], widgets['img_src'].pixels)
    if process_mode == 'L':
        widgets['img_proc'].pixels = filter_L(thresholds[thr_index], widgets['img_src'].pixels)
    if process_mode == 'A':
        widgets['img_proc'].pixels = filter_A(thresholds[thr_index], widgets['img_src'].pixels)
    if process_mode == 'B':
        widgets['img_proc'].pixels = filter_B(thresholds[thr_index], widgets['img_src'].pixels)
    
    clock.tick()

    # print(thr_buffer, clock.get_fps())
    
    # edit_index = constrain(edit_index, 0, len(thresholds[thr_index]) - 1)

    # if keys.get(pygame.K_w):
    #     thresholds[thr_index][edit_index] += 1
    # if keys.get(pygame.K_s):
    #     thresholds[thr_index][edit_index] -= 1
    
    thresholds[thr_index][0] = constrain(thresholds[thr_index][0], 0, 100)
    thresholds[thr_index][1] = constrain(thresholds[thr_index][1], 0, 100)
    thresholds[thr_index][2] = constrain(thresholds[thr_index][2], -127, 127)
    thresholds[thr_index][3] = constrain(thresholds[thr_index][3], -127, 127)
    thresholds[thr_index][4] = constrain(thresholds[thr_index][4], -127, 127)
    thresholds[thr_index][5] = constrain(thresholds[thr_index][5], -127, 127)

    if widgets['img_src'].selected_area is not None:
        widgets['label_coords'].text = 'Coords ' + str(widgets['img_src'].selected_area)

    widgets['label_mode'].text = 'Mode ' + process_mode

    for i in range(len(widgets['itemlist_thr'].items)):
        widgets['itemlist_thr'][i].text = f'Thr {i + 1}: ' + str(thresholds[i])

    L_low = widgets['slider_L_low'].value
    L_high = widgets['slider_L_high'].value
    widgets['label_L'].text = "L  [" + str(L_low) + ", " + str(L_high) + "]"

    A_low = widgets['slider_A_low'].value
    A_high = widgets['slider_A_high'].value
    widgets['label_A'].text = "A  [" + str(A_low) + ", " + str(A_high) + "]"

    B_low = widgets['slider_B_low'].value
    B_high = widgets['slider_B_high'].value
    widgets['label_B'].text = "B  [" + str(B_low) + ", " + str(B_high) + "]"
    
    thresholds[thr_index][0] = L_low
    thresholds[thr_index][1] = L_high
    thresholds[thr_index][2] = A_low
    thresholds[thr_index][3] = A_high
    thresholds[thr_index][4] = B_low
    thresholds[thr_index][5] = B_high
    
    for w in wnames:
        widgets[w].update()
    for w in wnames:
        widgets[w].draw()

    if widgets['img_src'].first_press is not None and widgets['img_src'].selected_area is not None:
        draw_rect_alpha(screen, (70, 100, 250, 100), widgets['img_src'].selected_area)
    
    pygame.display.update()

    if save_thr:
        save_thr = False
        print('SAVE')
        result = interface.call("save_thresholds", str(thresholds))
        if result is None:
            print('FAILED TO SAVE')
        else:
            print(str(bytes(result)))
        return


base_cam_arguments = "sensor.RGB565;sensor.QQVGA"
print(base_cam_arguments)
while(True):
    sys.stdout.flush()

    # You may change the pixformat and the framesize of the image transferred from the remote device
    # by modifying the below arguments.
    msg = base_cam_arguments + ";"
    result = interface.call("jpeg_image_stream", msg)
    print('send', msg)
    if result is not None:
        # THE REMOTE DEVICE WILL START STREAMING ON SUCCESS. SO, WE NEED TO RECEIVE DATA IMMEDIATELY.
        interface.stream_reader(jpg_frame_buffer_cb, queue_depth=8)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

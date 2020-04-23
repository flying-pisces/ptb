# -*- coding=utf-8 -*-

import numpy as np
import cv2
import sys
import os
import io
import shutil

out_put_dir = "img"

def generate_spot_img(name, bgcolor=(0, 0, 0), fgcolor=(0, 255, 0), height0=1920, width0=1824, spot = 2, spare_r = 0):
    blank_image = np.zeros((height0, width0, 3), np.uint8)
    blank_image[0:height0, 0:width0] = bgcolor
    height = height0
    width = width0 - spare_r
    for posx, posy in [(height/2, width/2), (height * 1/4, width * 1/4), (height * 3/4, width * 3/4),
                       (height * 1/4, width * 3/4),  (height * 3/4, width * 1/4)]:
        blank_image[posx-spot/2-1:posx-spot/2-1 + spot, posy-spot/2-1:posy-spot/2-1 + spot] = fgcolor

    bgst = ''.join([hex(c)[2:].zfill(2).upper() for c in bgcolor])
    fgst = ''.join([hex(c)[2:].zfill(2).upper() for c in fgcolor])
    cv2.imwrite(r"{}\{}_siz{}_bg{}_fg{}.bmp".format(out_put_dir, name, spot, bgst, fgst), blank_image)

#generate name is panel, color, grid size, brightness
#AUO

if os.path.exists(out_put_dir):
    shutil.rmtree(out_put_dir)

if not os.path.exists(out_put_dir):
    os.mkdir(out_put_dir, 0o777)

# image req for sequence setup.
for spot in [1, 10]:
    generate_spot_img('spot_', bgcolor=(0, 0, 0), fgcolor=(255, 0, 0), spot=spot, spare_r=24)
    generate_spot_img('spot_', bgcolor=(0, 0, 0), fgcolor=(0, 255, 0), spot=spot, spare_r=24)
    generate_spot_img('spot_', bgcolor=(0, 0, 0), fgcolor=(0, 0, 255), spot=spot, spare_r=24)

    generate_spot_img('spot_r', bgcolor=(255, 255, 255), fgcolor=(255, 255, 0), spot=spot, spare_r=24)
    generate_spot_img('spot_r', bgcolor=(255, 255, 255), fgcolor=(0, 255, 0), spot=spot, spare_r=24)
    generate_spot_img('spot_r', bgcolor=(255, 255, 255), fgcolor=(255, 0, 255), spot=spot, spare_r=24)

print ('All image is been generated.')

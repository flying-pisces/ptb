## Generate all the test patterns to be used in MOT station

import cv2
import numpy as np
import matplotlib.pyplot
from matplotlib.pyplot import plot as plt
h = 1920
w = 1824
blank_image = np.zeros((h, w, 3), np.uint8)

# White
white = (255, 255, 255)
blank_image[0:h, 0:w] = white
cv2.imwrite("white.bmp", blank_image)
# Gray 127
gray127 = (127, 127, 127)
blank_image[0:h, 0:w] = gray127
cv2.imwrite("gray127.bmp", blank_image)
# Black
black = (0, 0, 0)
blank_image[0:h, 0:w] = black
cv2.imwrite("black.bmp", blank_image)

# Blue
blue = (255, 0, 0)
blank_image[0:h, 0:w] = blue
cv2.imwrite("blue.bmp", blank_image)
# Green
green = (0, 255, 0)
blank_image[0:h, 0:w] = green
cv2.imwrite("green.bmp", blank_image)
# Red
red = (0, 0, 255)
blank_image[0:h, 0:w] = red
cv2.imwrite("red.bmp", blank_image)
# Combo RGB
blank_image[0:h, 0:int(w/3)] = red
blank_image[0:h, int(w/3)+1:int(w/3*2)] = green
blank_image[0:h, int(w/3*2)+1:w] = blue
cv2.imwrite("comborgb.bmp", blank_image)
# WhiteCACCorrect-Contrast
contrast_fg = (255,255,255)
contrast_bg= (0,0,0)
grid_x = 4
grid_y = 4
name = "white-cac-corrected-contrast"
blank_image = np.zeros((h, w, 3), np.uint8)
blank_image[0:h, 0:w] = contrast_bg
block_x = int(w/grid_x)
block_y = int(h/grid_y)
for ix in range(0, grid_x):
    for jy in range(0, grid_y):
        if (ix+jy)%2 == 0:
            blank_image[jy*block_y:(jy+1)*block_y, ix*block_x:(ix+1)*block_x] = contrast_bg
        else:
            blank_image[jy*block_y:(jy+1)*block_y, ix*block_x:(ix+1)*block_x] = contrast_fg
cv2.imwrite("{}_{}_by_{}.bmp".format(name, grid_y, grid_x), blank_image)
# Green-Contrast
contrast_fg = (0,255,0)
contrast_bg= (0,0,0)
grid_x = 4
grid_y = 4
name = "green-contrast"
blank_image = np.zeros((h, w, 3), np.uint8)
blank_image[0:h, 0:w] = contrast_bg
block_x = int(w/grid_x)
block_y = int(h/grid_y)
for ix in range(0, grid_x):
    for jy in range(0, grid_y):
        if (ix+jy)%2 == 0:
            blank_image[jy*block_y:(jy+1)*block_y, ix*block_x:(ix+1)*block_x] = contrast_bg
        else:
            blank_image[jy*block_y:(jy+1)*block_y, ix*block_x:(ix+1)*block_x] = contrast_fg
cv2.imwrite("{}_{}_by_{}.bmp".format(name, grid_y, grid_x), blank_image)
# Green-Sharpness
contrast_fg = (0,255,0)
contrast_bg = (0,0,0)
grid_x = 4
grid_y = 4
name = "green-sharpness"
blank_image = np.zeros((h, w, 3), np.uint8)
blank_image[0:h, 0:w] = contrast_bg
block_x = int(w/grid_x)
block_y = int(h/grid_y)
for ix in range(0, grid_x):
    blank_image[0:h, ix*block_x:ix*block_x+1] = contrast_fg
for iy in range(0, grid_y):
    blank_image[iy*block_y:iy*block_y+1, 0:w] = contrast_fg
cv2.imwrite("{}_{}_by_{}.bmp".format(name, grid_y, grid_x), blank_image)

# Distortion
# The distortion matrix that I vary
from wand.image import Image

with Image(filename="green4by4.bmp") as img:
    print(img.size)
    img.virtual_pixel = 'transparent'
    img.distort('barrel', (0.2, 0.0, 0.0, 1.0))
    img.save(filename='distortion.bmp')
    # convert to opencv/numpy array format
    img_opencv = np.array(img)

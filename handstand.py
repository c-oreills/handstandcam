import sys

import cv2
import numpy as np

ESCAPE_KEY = 1048603

SV_MIN = np.array([0, 80, 80],np.uint8)
SV_MAX = np.array([0, 255, 255],np.uint8)

HUE_WIDTH = 10

camera = None
current_capture = None
current_hue_pix = np.array([55, 255, 255],np.uint8)

def _convert_pixel(pixel, color_space):
    arr = np.array([[pixel]], np.uint8)
    new_pixel = cv2.cvtColor(arr, color_space)[0][0]
    return new_pixel

def hsv_to_bgr(pixel):
    return _convert_pixel(pixel, cv2.COLOR_HSV2BGR)

def bgr_to_hsv(pixel):
    return _convert_pixel(pixel, cv2.COLOR_BGR2HSV)

def col(pixel, hsv=False):
    if hsv:
        pixel = hsv_to_bgr(pixel)
    return tuple(int(c) for c in pixel)

def setup():
    global camera
    camera = cv2.VideoCapture(0)
    cv2.namedWindow('output')
    cv2.namedWindow('capture')
    cv2.setMouseCallback('capture', hue_select_callback)

def hue_select_callback(event, x, y, ch, o):
    if event == cv2.EVENT_LBUTTONUP:
        select_hue(x, y)

def select_hue(x, y):
    pixel = current_capture[y, x]
    hue_pix = bgr_to_hsv(pixel)

    global current_hue_pix
    current_hue_pix = hue_pix

def get_hues():
    hue_min = SV_MIN.copy()
    hue_min[0] = current_hue_pix[0] - HUE_WIDTH
    hue_max = SV_MAX.copy()
    hue_max[0] = current_hue_pix[0] + HUE_WIDTH
    return hue_min, hue_max

def get_image():
   retval, im = camera.read()
   return im

def calc_central_moments(moments):
    x = moments['m10']/moments['m00']
    y = moments['m01']/moments['m00']
    return x, y

def do_frame():
    global current_capture
    current_capture = get_image()
    cv2.imshow('capture', current_capture)
    blur_img = cv2.blur(current_capture, (5, 5))
    hsv_img = cv2.cvtColor(blur_img, cv2.COLOR_BGR2HSV)

    hue_min, hue_max = get_hues()
    thresh_img = cv2.inRange(hsv_img, hue_min, hue_max)
    out = np.zeros(current_capture.shape, np.uint8)
    cv2.add(out, current_capture, dst=out, mask=thresh_img)
    hsv_pixel = current_hue_pix.copy()
    hsv_pixel[1] = hsv_pixel[2] = 255
    bgr_hue = col(hsv_pixel, hsv=True)
    hsv_pixel[0] += 90
    hsv_pixel[0] %= 180
    bgr_complement = col(hsv_pixel, hsv=True)
    cv2.rectangle(out, (0, 0), (10, 10), bgr_hue, -1)
    contours, hierarchy = cv2.findContours(thresh_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        big_contours = [c for c in contours if cv2.contourArea(c) > 1000]
        cv2.drawContours(out, big_contours, -1, bgr_complement)
        moments = [cv2.moments(c) for c in big_contours]
        central_moments = [calc_central_moments(m) for m in moments]
        for x, y in central_moments:
            cv2.circle(out, (int(x), int(y)), 15, bgr_complement, -1)

    cv2.imshow('output', out)
    key = cv2.waitKey(50)
    if key == ESCAPE_KEY:
        sys.exit()

setup()
while True:
    do_frame()

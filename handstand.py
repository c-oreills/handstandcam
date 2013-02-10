from collections import Counter
import sys

import cv2
import numpy as np

ESCAPE_KEY = 1048603

HUE_MIN = np.array([45, 50, 50],np.uint8)
HUE_MAX = np.array([70, 255, 255],np.uint8)

SV_MIN = np.array([0, 50, 50],np.uint8)
SV_MAX = np.array([0, 255, 255],np.uint8)

camera = None
current_capture = None

def setup():
    global camera
    camera = cv2.VideoCapture(0)
    cv2.namedWindow('capture')
    cv2.namedWindow('output')
    cv2.namedWindow('selection')
    cv2.setMouseCallback('capture', start_select_callback)

def start_select_callback(event, x, y, ch, o):
    if event == cv2.EVENT_LBUTTONDOWN:
        start_select(x, y)

def start_select(start_x, start_y):
    def end_select_callback(event, x, y, ch, o):
        if event == cv2.EVENT_LBUTTONUP:
            end_select(start_x, start_y, x, y)

    cv2.setMouseCallback('capture', end_select_callback)

def end_select(start_x, start_y, end_x, end_y):
    select (start_x, start_y, end_x, end_y)
    cv2.setMouseCallback('capture', start_select_callback)

def select(x1, y1, x2, y2):
    l, r = sorted((x1, x2))
    t, b = sorted((y1, y2))
    selection = current_capture[t:b, l:r]
    selection_blur = cv2.blur(selection, (3, 3))
    selection_hsv = cv2.cvtColor(selection_blur, cv2.COLOR_BGR2HSV)
    selection_hues, _, _ = cv2.split(selection_hsv)
    hue_counter = Counter()
    BUCKET_WIDTH = 5
    def bucket(hue):
        MAX_BUCKET = 180 / BUCKET_WIDTH
        b = hue / BUCKET_WIDTH
        # handle under and overflow
        if b < 0:
            b = MAX_BUCKET
        if b > MAX_BUCKET:
            b = 0
        return b
    @np.vectorize
    def count_hues(hue):
        hue_counter[bucket(hue)] += 1
        hue_counter[bucket(hue) + BUCKET_WIDTH] += 1
        hue_counter[bucket(hue) - BUCKET_WIDTH] += 1
    count_hues(selection_hues)
    [(prevalent_bucket, _)] = hue_counter.most_common(1)
    prevalent_hue = prevalent_bucket * BUCKET_WIDTH
    print 'prev_hue', prevalent_hue
    hue_min = prevalent_hue - BUCKET_WIDTH
    hue_max = prevalent_hue + (2 * BUCKET_WIDTH)
    HUE_MIN[0] = hue_min
    HUE_MAX[0] = hue_max

    selection_hue_thresh = cv2.inRange(selection, HUE_MIN, HUE_MAX)
    selection_out = cv2.bitwise_and(selection, selection, mask=selection_hue_thresh)

    cv2.imshow('selection', selection_out)

def get_image():
   retval, im = camera.read()
   return im

def do_frame():
    global current_capture
    current_capture = get_image()
    cv2.imshow('capture', current_capture)
    hsv_img = cv2.cvtColor(current_capture, cv2.COLOR_BGR2HSV)

    thresh_img = cv2.inRange(hsv_img, HUE_MIN, HUE_MAX)
    out = cv2.bitwise_and(current_capture, current_capture, mask=thresh_img)

    cv2.imshow('output', out)
    key = cv2.waitKey(50)
    if key == ESCAPE_KEY:
        sys.exit()

setup()
while True:
    do_frame()

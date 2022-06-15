import cv2
import numpy as np

def update_img(color, frame):
    img_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    cv2.imshow('mask', img_mask)

    img_layed = cv2.bitwise_and(frame, frame, mask=img_mask)
    cv2.imshow('masked', img_layed)

def update(window_name, frame, value = 0):
    color_low = (
        cv2.getTrackbarPos('h_min', window_name),
        cv2.getTrackbarPos('s_min', window_name),
        cv2.getTrackbarPos('v_min', window_name)
    )

    color_high = (
        cv2.getTrackbarPos('h_max', window_name),
        cv2.getTrackbarPos('s_max', window_name),
        cv2.getTrackbarPos('v_max', window_name)
    )
    color = (color_low, color_high)

    update_img(color, frame)

    return color
# 
def correction(window_name):
    cv2.namedWindow(window_name)
    cv2.createTrackbar('h_min', window_name,   0, 180, update)
    cv2.createTrackbar('s_min', window_name,   0, 255, update)
    cv2.createTrackbar('v_min', window_name,   0, 255, update)
    cv2.createTrackbar('h_max', window_name, 180, 180, update)
    cv2.createTrackbar('s_max', window_name, 255, 255, update)
    cv2.createTrackbar('v_max', window_name, 255, 255, update)

if __name__ == '__main__':
    # video = cv2.VideoCapture(0)
    window_name = 'Correction'
    correction(window_name)
    while True:
        # _, frame = video.read()
        frame = cv2.imread("black.png")
        color = update(window_name, frame)
        
        key_press = cv2.waitKey(30)
        if key_press == ord('q'):
            # cv2.imwrite('hsv.jpg', hsv)
            break
import cv2
import numpy as np
import math
from videoserver import VideoServer
import pymurapi as mur

auv = mur.mur_init()

mur_view = VideoServer()

def detect_shape(cnt):
    try:
        area = cv2.contourArea(cnt)

        if area < 500:
            return None

        rectangle = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rectangle)
        box = np.int0(box)
        rectangle_area = cv2.contourArea(box)
        rect_w, rect_h = rectangle[1][0], rectangle[1][1]
        aspect_ratio = max(rect_w, rect_h) / min(rect_w, rect_h)

        shapes_areas = {
            'rectangle' if aspect_ratio > 1.2 else 'square': rectangle_area,
        }

        diffs = {
            name: abs(area - shapes_areas[name]) for name in shapes_areas
        }

        shape_name = min(diffs, key=diffs.get)

        # line_color = (255,255,255)

        # if shape_name == 'rectangle' or shape_name == 'square':
            # cv2.drawContours(drawing, [box], 0, line_color, 2, cv2.LINE_AA)

        return shape_name
    except:
        return None

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def get_center(img, contours):
    areas = [
        cv2.contourArea(cnt1) if (detect_shape(cnt1) == 'rectangle') else 0 for cnt1 in contours
    ]
    
#    contours1 = [
#        cnt1 if (detect_shape(cnt1) == 'rectangle') else 0 for cnt1 in contours
#    ]

    if (len(areas) > 0):
        cnt_max = contours[np.argmax(areas)]
#        print(cnt2)
        rectangle = cv2.minAreaRect(cnt_max)
        box = cv2.boxPoints(rectangle)
        box = np.int0(box)
        cv2.drawContours(img, [box], 0, (0, 0, 255), 2, cv2.LINE_AA)
        
        center_point = ((box[0, 0] + box[1, 0] + box[2, 0] + box[3, 0]) // 4, (box[0, 1] + box[1, 1] + box[2, 1] + box[3, 1]) // 4)

        # cv2.circle(img, box[0], 3, (0, 255, 0), -1)
        # cv2.circle(img, box[1], 3, (0, 255, 0), -1)
        # cv2.circle(img, box[2], 3, (0, 255, 0), -1)
        # cv2.circle(img, box[3], 3, (0, 255, 0), -1)
        cv2.circle(img, center_point, 3, (0, 255, 0), -1)
        return center_point
    raise ValueError

def stabilization(pt, up, down):
    y = pt[1]
    middle = up + (abs(down - up)//2)
    power = max(min((y-middle) * 0.25, 50), -50)
    return power



if __name__ == '__main__':    
    color_orange_evening = (
        (0, 0, 0),
        (19, 255, 230)
    )

    color_orange_day = (
        (0, 0, 90),
        (31, 255, 255)
    )

    video1 = cv2.VideoCapture(0)
    video2 = cv2.VideoCapture(1)
    _, frame1 = video1.read()

    up = (7 * len(frame1)) // 16
    down = (9 * len(frame1)) // 16
    while True:
        _, frame1 = video1.read()
        _, frame2 = video2.read()
        cnt = find_contours(frame2, color_orange_day)

        try:
            center_point = get_center(frame2, cnt)
            power = stabilization(center_point, up, down)
            
            auv.set_motor_power(1, power)
            auv.set_motor_power(2, power)

            cv2.line(frame2, (0, up), (len(frame2[0]), up), (0, 0, 255), 3)
            cv2.line(frame2, (0, down), (len(frame2[0]), down), (0, 0, 255), 3)

        except ValueError:
            pass
        mur_view.show(frame2, 1)
        
        
        
        
        
        
        
        

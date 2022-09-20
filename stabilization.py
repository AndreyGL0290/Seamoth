# from videoserver import VideoServer
import pymurapi as mur
import numpy as np
import math
import time
import cv2

auv = mur.mur_init()
IS_AUV = False

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def detect_shape(drawing, cnt):
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

        line_color = (255,255,255)

        if shape_name == 'rectangle' or shape_name == 'square':
            cv2.drawContours(drawing, [box], 0, line_color, 2, cv2.LINE_AA)

        return shape_name
    except:
        return None

# Функция для вычисления угла отклонения от полоски.
def calc_angle(drawing, cnt):
    try:
        rectangle = cv2.minAreaRect(cnt)

        box = cv2.boxPoints(rectangle)
        box = np.int0(box)
        cv2.drawContours(drawing, [box], 0, (0,0,255), 3)

        # К сожалению, мы не можем использовать тот угол,
        # который входит в вывод функции minAreaRect,
        # т.к. нам необходимо ориентироваться именно по
        # длинной стороне полоски. Находим длинную сторону.

        edge_first = np.int0((box[1][0] - box[0][0], box[1][1] - box[0][1]))
        edge_second = np.int0((box[2][0] - box[1][0], box[2][1] - box[1][1]))

        edge = edge_first
        if cv2.norm(edge_second) > cv2.norm(edge_first):
            edge = edge_second

        # Вычисляем угол по длинной стороне.
        angle = -((180.0 / math.pi * math.acos(edge[0] / (cv2.norm((1, 0)) * cv2.norm(edge)))) - 90)

        return angle if not math.isnan(angle) else 0
    except:
        return 0

if __name__ == '__main__':
    color = (
        (0, 0, 0),
        (17, 255, 255)
    )
    video1 = cv2.VideoCapture(0)

    while True:
        _, img = video1.read()

        drawing = img.copy()
        contours = find_contours(img, color)

        angle = 0

        if contours:
            # Вычисляем площадь для каждого контура, а затем берём контур с наибольшей
            # площадью, но только если он совпадает с искомой фигурой.
            areas = [
                cv2.contourArea(cnt) if (detect_shape(drawing, cnt) == 'rectangle') else 0 for cnt in contours
            ]

            if (len(areas) > 0) and (max(areas) > 500):
                cnt = contours[np.argmax(areas)]

                angle = calc_angle(drawing, cnt)

                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(drawing, 'angle: %d' % angle, (5, 30), font, 1, (255,255,255), 1, cv2.LINE_AA)
        if IS_AUV:
            power = max(min(angle * 0.75, 50), -50)
            auv.set_motor_power(1, -power)
            auv.set_motor_power(2,  power)
        else:
            cv2.imshow('img', drawing)
            key_pressed = cv2.waitKey(30)
            if key_pressed == ord("q"):
                break
    
    video1.release()
    print("done")
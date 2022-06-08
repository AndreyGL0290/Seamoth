import pymurapi as mur
from videoserver import VideoServer
import numpy as np
import math
import time
import cv2

auv = mur.mur_init()
mur_view = VideoServer()

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    
    # img_layed = cv2.bitwise_and(img, img, mask=img_mask)
    # cv2.imshow('masked', img_layed)
    
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def search(color, img):
    circles = 0
    rect = 0
    # drawing = img.copy()
    contours = find_contours(img, color)
    for cnt in contours:
#        print(cnt)
        area = cv2.contourArea(cnt)

        if area < 300:
            continue

        # Описанная окружность.
        (circle_x, circle_y), circle_radius = cv2.minEnclosingCircle(cnt)
        circle_area = circle_radius ** 2 * math.pi

        # Описанный прямоугольник (с вращением)
        rectangle = cv2.minAreaRect(cnt)

        # Получим контур описанного прямоугольника
        box = cv2.boxPoints(rectangle)
        box = np.int0(box)

        # Вычислим площадь и соотношение сторон прямоугольника.
        rectangle_area = cv2.contourArea(box)
        rect_w, rect_h = rectangle[1][0], rectangle[1][1]
        aspect_ratio = max(rect_w, rect_h) / min(rect_w, rect_h)


        # Заполним словарь, который будет содержать площади каждой из описанных фигур
        shapes_areas = {
            'circle': circle_area,
            'rect' if aspect_ratio > 1.25 else 'square': rectangle_area,
        }

        # Теперь заполним аналогичный словарь, который будет содержать
        # разницу между площадью контора и площадью каждой из фигур.
        diffs = {
            name: abs(area - shapes_areas[name]) for name in shapes_areas
        }

        # Получаем имя фигуры с наименьшей разницой площади.
        shape_name = min(diffs, key=diffs.get)

        if shape_name == 'circle':
            circles += 1

        if shape_name == 'rect' or shape_name == 'square':
            rect += 1
        # cv2.imshow('frame', img)
        # cv2.waitKey(30)
    return circles, rect

def LED(times, color):
    auv.set_on_delay(1)
    auv.set_off_delay(0.5)
    auv.set_rgb_color(color[0], color[1], color[2])
    if times == 1:
        time.sleep(times)
    time.sleep(times*1.5)
    auv.set_off_delay(0)
    auv.set_rgb_color(0, 255, 0)

if __name__ == '__main__':
    video1 = cv2.VideoCapture(0)
    _, frame1 = video1.read()
    color_black = (
        (50, 0, 0),
        (97, 104, 53)
    )
    circles, rects = search(color_black, frame1)
    print(circles, rects)
    LED(circles, (255, 0, 0))
#    while True:
#        _, frame1 = video1.read()
#        mur_view.show(frame1, 0)

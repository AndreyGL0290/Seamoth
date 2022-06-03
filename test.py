import cv2
import math
from cv2 import waitKey
import numpy as np

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def search(shape, color, img):
    circles = 0
    rect = 0
    # drawing = img.copy()
    contours = find_contours(img, color)
    for cnt in contours:
        print(cnt)
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
        
        line_color = (0,0,255)
        
        # Нарисуем соответствующую описанную фигуру вокруг контура

        if shape_name == 'circle' and shape == 'circle':
            cv2.circle(img, (int(circle_x), int(circle_y)), int(circle_radius), line_color, 2, cv2.LINE_AA)
            # circles += 1

        if (shape_name == 'rect' or shape_name == 'square') and (shape == 'rect' or shape == 'square'):
            cv2.drawContours(img, [box], 0, line_color, 2, cv2.LINE_AA)
            # rect += 1
        # cv2.imshow('frame', img)
        # cv2.waitKey(30)
    if shape == 'rect':
        return rect
    else:
        return circles

# КОД ДЛЯ КАРТИНОК В ПРЕЗЕНТАЦИИ
if __name__ == '__main__':
    video = cv2.VideoCapture(0)

    color_black = (
        (0, 0, 0),
        (180, 255, 90)
    )

    color_red2 = (
        (0, 0, 0),
        (180, 160, 130)
    )
    frame = cv2.imread('red2.png')
    # while True:
    #     _, frame = video.read() 
    search('circle', color_red2, frame)
    cv2.imshow('frame', frame)
    cv2.waitKey(0)

    # print('BIN - {:08b}\nOCT - {:o}\nHEX - {:x}\nFLOAT - {:0.3f}'.format(120, 120, 120, 120.1235))
    # for i in range(100):
    #     if i % 3 == 0 and i % 4 == 0 and i % 5 == 0:
    #         print(i)
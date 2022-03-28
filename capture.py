import cv2
from cv2 import circle
import numpy as np
import math
from correction import update, correction

def search(shape, color, frame):
    contours = find_contours(frame, color, shape)
    for cnt in contours:
        area = cv2.contourArea(cnt)

        if area < 500:
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
            cv2.circle(frame, (int(circle_x), int(circle_y)), int(circle_radius), line_color, 2, cv2.LINE_AA)

        if (shape_name == 'rect' or shape_name == 'square') and (shape == 'rect' or shape == 'square'):
            cv2.drawContours(frame, [box], 0, line_color, 2, cv2.LINE_AA)

        # вычислим центр, нарисуем в центре окружность и ниже подпишем
        # текст с именем фигуры, которая наиболее похожа на исследуемый контур.

        moments = cv2.moments(cnt)
        if shape_name == shape:
            try:
                x = int(moments['m10'] / moments['m00'])
                y = int(moments['m01'] / moments['m00'])
                cv2.circle(frame, (x,y), 4, line_color, -1, cv2.LINE_AA)

                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(frame, shape_name, (x-40, y+31), font, 1, (  0,  0,  0), 4, cv2.LINE_AA)
                cv2.putText(frame, shape_name, (x-41, y+30), font, 1, (255,255,255), 2, cv2.LINE_AA)
            except ZeroDivisionError:
                pass

def find_contours(img, color, shape='image'):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # print('Круг: ', img_hsv[200, 480])
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    cv2.imshow(f'{shape} mask', img_mask)
    cv2.imshow(f'{shape} hsv', img_hsv)
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return contours

if __name__ == '__main__':
    video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    window_name = 'image'
    correction(window_name)
    while True:
        _, frame = video.read()
        cv2.imshow(window_name, frame)
        color = update(window_name, frame)
        # ret, frame = video.read()


        drawing1 = frame.copy()
        # drawing2 = frame.copy()
        # # Кванториум белый
        # # color = (
        # #     (10, 0, 20),
        # #     (160, 50, 255)
        # # )

        # # Кванториум черный
        # color_black = (
        #     ( 0, 0,  0),
        #     ( 255, 255, 70)
        # )

        # color_orange = (
        #     ( 0, 140,  100),
        #     ( 12, 255, 255)
        # )

        # # color = (
        # #     (10, 40, 20),
        # #     (160, 70, 95)
        # # )

        search('circle', color, drawing1)
        # search('rect', color_orange, drawing2)
        cv2.imshow('drawing1', drawing1)
        # cv2.imshow('drawing2', drawing2)

        # # cv2.imshow('video', frame)


        # # hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # # mask1 = cv2.inRange(hsv, (50, 70, 0), (135, 255, 160))

        # # target = cv2.bitwise_and(frame, frame, mask=mask1)

        # # cv2.imshow('MASK', mask1)
        # # cv2.imshow('USUAL', frame)
        # # cv2.imshow('FINAL', target)
        # # cv2.imshow('HSV', hsv)
        key_press = cv2.waitKey(30)
        if key_press == ord('q'):
            # cv2.imwrite('hsv.jpg', hsv)
            break

    video.release()
    cv2.destroyAllWindows()

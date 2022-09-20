import cv2
import numpy as np
import mss
import math

from shape import find_contours


with mss.mss() as sct:

    monitor = {"top": 540, "left": 1162, "width": 558, "height": 410} # Для ноутбука без доп экрана
    # monitor = {"top": 115, "left": -749, "width": 541, "height": 406} # Для ноутбука с доп экраном
    circles = 0
    rects = 0
    frames = 0
    n = 1
    while "Screen capturing":
        frames += 1
        img = np.array(sct.grab(monitor))
        height = len(img)
        width = len(img[0])
        # img = img[height//2-20:height//2+20, width//2-20:width//2+20]
        img = img
        drawing = img.copy()
        # Черный
        # color = (
        #     ( 0, 0,  0),
        #     ( 100, 255, 50)
        # )
        
        # Белый
        # color = (
        #     (20, 0, 0),
        #     (180, 255, 255)
        # )

        # Оранжевый
        color = (
            ( 15, 20,  20),
            ( 25, 255, 255)
        )

        contours = find_contours(img, color)

        if contours:
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
                    'rectangle' if aspect_ratio > 1.25 else 'square': rectangle_area,
                }

                # Теперь заполним аналогичный словарь, который будет содержать
                # разницу между площадью контора и площадью каждой из фигур.
                diffs = {
                    name: abs(area - shapes_areas[name]) for name in shapes_areas
                }

                # Получаем имя фигуры с наименьшей разницой площади.
                shape_name = min(diffs, key=diffs.get)

                line_color = (0,100,255)

                # Нарисуем соответствующую описанную фигуру вокруг контура

                if shape_name == 'circle':
                    cv2.circle(drawing, (int(circle_x), int(circle_y)), int(circle_radius), line_color, 2, cv2.LINE_AA)
                    circles += 1

                if shape_name == 'rectangle' or shape_name == 'square':
                    cv2.drawContours(drawing, [box], 0, line_color, 2, cv2.LINE_AA)
                    rects += 1

                # вычислим центр, нарисуем в центре окружность и ниже подпишем
                # текст с именем фигуры, которая наиболее похожа на исследуемый контур.

                moments = cv2.moments(cnt)

                try:
                    x = int(moments['m10'] / moments['m00'])
                    y = int(moments['m01'] / moments['m00'])
                    cv2.circle(drawing, (x,y), 4, line_color, -1, cv2.LINE_AA)

                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(drawing, shape_name, (x-40, y+31), font, 1, (  0,  0,  0), 4, cv2.LINE_AA)
                    cv2.putText(drawing, shape_name, (x-41, y+30), font, 1, (255,255,255), 2, cv2.LINE_AA)
                except ZeroDivisionError:
                    pass

        cv2.imshow('drawing', drawing)

        # print(frames, n)
    # показываем кадр в окне ’Video’
        cv2.imshow('Video', img)
        if frames == 300 * n:
            # print(circles//frames)
            print(rects//frames)
            circles = 0
            rects = 0
            frames = 0
    # организуем выход из цикла по нажатию клавиши,
    # ждем 30 миллисекунд нажатие, записываем код
    # нажатой клавиши

    # если код нажатой клавиши совпадает с кодом
    # «q»(quit - выход),
        if cv2.waitKey(25) & 0xFF == ord("q"):
            cv2.destroyAllWindows()
            break
    # освобождаем память от переменной capImg


        # hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # # mask1 = cv2.inRange(hsv, (50, 70, 0), (135, 255, 160)) # Для черного цвета
        # mask1 = cv2.inRange(hsv, (0,0,0), (180,255,100)) # Для всех (почти), кроме белых пикселей
        # target = cv2.bitwise_and(img, img, mask=mask1)

        # cv2.imshow('MASK1', mask1)
        # cv2.imshow('USUAL', img)
        # # cv2.imshow('FINAL', target)
        # cv2.imshow('HSV', hsv)

        # contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        # # print(len(contours))
        # box1 = []
        # # перебираем все найденные контуры в цикле
        # for i in range(len(contours)):
        #     # ищем прямоугольник, результат записываем
        #     # в rect
        #     rect = cv2.minAreaRect(contours[i]) 
        #     # вычисление площади прямоугольного контура
        #     area = int(rect[1][0]*rect[1][1]) 
        #     # ФИЛЬТРУЕМ МЕЛКИЕ КОНТУРЫ
        #     # отсекаем ложные контуры, если они вдруг
        #     # появятся
        #     if area > 200:
        #         box1.append(contours[i])
        #         # рисуем прямоугольник
        #         cv2.drawContours(img, contours, i, (0,0,255), 20)

        # # print('Тень: ', hsv[360, 0], 'Круг: ', hsv[70, 480])
        # print(len(box1))

# video = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# while True:
    # ret, img = video.read()

    # hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # mask1 = cv2.inRange(hsv, (50, 70, 0), (135, 255, 160))

    # target = cv2.bitwise_and(img, img, mask=mask1)

    # cv2.imshow('MASK', mask1)
    # cv2.imshow('USUAL', img)
    # cv2.imshow('FINAL', target)
    # cv2.imshow('HSV', hsv)
    # print('Тень: ', hsv[360, 0], 'Круг: ', hsv[70, 480])
#     key_press = cv2.waitKey(30)
#     if key_press == ord('q'):
#         cv2.imwrite('hsv.jpg', hsv)
#         break

# video.release()
# cv2.destroyAllWindows()

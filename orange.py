import cv2
import numpy as np
import time
import math
import pymurapi as mur
from videoserver import VideoServer

auv = mur.mur_init()
mur_view = VideoServer()
IS_AUV = True
HAVE_AUV_VIDEO_SERVER = True

# try:
#    import pymurapi as mur
#    auv = mur.mur_init()
#    mur_view = auv.get_videoserver()
#    IS_AUV = True

#    try:
#        mur_view = auv.get_videoserver()
#        HAVE_AUV_VIDEO_SERVER = True
#    except AttributeError:
#        HAVE_AUV_VIDEO_SERVER = False

# except ImportError:
#    IS_AUV = False

def clamp(value, min, max):
    if value <= min :
        return min - value % min
    if value >= max:
        return max - value % min
    return value

def turn(drawing, side='control'):
    contours = find_contours(frame2, color)

    angle = 0

    if contours:
        # Вычисляем площадь для каждого контура, а затем берём контур с наибольшей
        # площадью, но только если он совпадает с искомой фигурой.
        areas = [
            cv2.contourArea(cnt) if (detect_shape(cnt) == 'rectangle') else 0 for cnt in contours
        ]
#        print(areas)
        if (len(areas) > 0) and (max(areas) > 300):
            cnt = contours[np.argmax(areas)]

            angle = calc_angle(drawing, cnt)

            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(drawing, 'angle: %d' % angle, (5, 30), font, 1, (255,255,255), 1, cv2.LINE_AA)
            # if 0<angle<=45 or -90<angle<-45: # ДВУХСТОРОННИЙ ПОВОРОТ
            #     print("Turn left")
            # elif angle == 0 or angle == 90:
            #     print("Stop")
            # elif 45<angle<90 or -45<angle<0:
            #     print('Turn right')

            # if angle<0: # ОДНОСТОРОННИЙ ПОВОРОТ К 0 ГРАДУСОВ
            #     print("Turn left")
            # elif angle == 0:
            #     print("Stop")
            # elif angle>0:
            #     print('Turn right')

            if IS_AUV:
                # Задаём тягу, прямо пропорциональную найденному углу отклонения.
                # Чем больше отклонение, тем сильнее будет тяга на движителях.
                #
                # angle - отклонение угла аппарата от угла вращения полоски.
                power = max(min(angle * 0.75, 50), -50)
                auv.set_motor_power(1, -power)
                auv.set_motor_power(2, power)
                
                
                
                # a = 0
                # if side == 'left':
                #     if 0<=angle<90:
                #         print('Turn rigth')
                #         auv.set_motor_power(1, -power)
                #         auv.set_motor_power(2, power)
                #     elif -90<angle<0:
                #         print('Turn left')
                #         auv.set_motor_power(1, power)
                #         auv.set_motor_power(2, -power)
                #     elif angle == 90:
                #         print('stop')
                # else:
                #     if angle<0:
                #         print('Turn left')
                #         auv.set_motor_power(1, -power)
                #         auv.set_motor_power(2, power)
                #     elif angle > 0:
                #         print('Turn right')
                #         auv.set_motor_power(1, power)
                #         auv.set_motor_power(2, -power)
                #     elif angle == 0 or angle == 90:
                #         print('Stop')


                # Таким образом, у нас получился простейший
                # пропорциональный регулятор (proportional controller, он же P-регулятор).

#                if HAVE_AUV_VIDEO_SERVER:
#                    mur_view.show(drawing, 1)
    return angle


def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return contours

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

# Функция для вычисления угла отклонения от полоски.
def calc_angle(drawing, cnt):
    try:
        rectangle = cv2.minAreaRect(cnt)

        box = cv2.boxPoints(rectangle)
        box = np.int0(box)
        cv2.drawContours(drawing, [box], 0, (0,0,255), 3)
        # print(box)
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
        (0,  0,  98),
        (31, 248, 255),
    )
    color_outside = (
        (0, 141, 144),
        (17, 255, 255)
    )
    video1 = cv2.VideoCapture(0) # Нижняя
    video2 = cv2.VideoCapture(1) # Передняя
#    cap = cv2.VideoCapture(0)

    while True:
        _, frame1 = video1.read()
        _, frame2 = video2.read()
        
        drawing = frame2.copy()

        angle = turn(drawing)

        mur_view.show(frame1, 0) # ДЛЯ РОБОТА
        mur_view.show(drawing, 1) # ДЛЯ РОБОТА
        if -3<angle<3:
            break
#        cv2.imshow('img', drawing)
#        key_press = cv2.waitKey(30)
#        if key_press == ord('q'):
#            break
    # now = time.time * 1000
    # while time.time()-now < 3:
    #     _, frame1 = video1.read()
    #     _, frame2 = video2.read()
    #     auv.set_motor_power(1, -20)
    #     auv.set_motor_power(2, -20)


    # video1.release()
    # video2.release()
    
    print("done")
    
    
    

from videoserver import VideoServer
import pymurapi as mur
import numpy as np
import math
import time
import cv2

IS_AUV = True

auv = mur.mur_init()

mur_view = VideoServer()

prev_time = 0
prev_high_diff = 0

def clamp(power, max, min):
    if power >= max:
        return max
    elif power < min:
        return min
    return power

def to_180(a):
    if a > 180.0:
        return a - 360
    if a < -180.0:
        return a + 360
    return a

class PD(object):
    _kp = 0.0
    _kd = 0.0
    _prev_error = 0.0
    _timestamp = 0
    
    def __init__(self):
        pass
    def set_p_gain(self, value):
        self._kp = value
        
    def set_d_gain(self, value):
        self._kd = value
        
    def process(self, error):
        timestamp = int(round(time.time() * 1000))
        output= self._kp * error + self._kd / (timestamp - self._timestamp) * (error - self._prev_error)
        self._timestamp = timestamp
        self._prev_error = error 
        return output

def keep_depth(depth):
    global prev_time, prev_high_diff
    current_time = int(round(time.time() * 1000))
    k = 100
    high_diff = auv.get_depth() - depth

    power_0 = 0
    power_3 = 0

    diff_value = 10 / (current_time - prev_time) * (high_diff - prev_high_diff)
#    if abs(high_diff) < 0.2:
#        k = 200
    power_value = clamp(high_diff*k + diff_value, 100, -100)
    power_0 = power_value
    power_3 = power_value
    
#    print(power_0, power_3)
    
    auv.set_motor_power(0, power_0)
    auv.set_motor_power(3, power_3)

    prev_time = current_time
    prev_high_diff = high_diff

def keep_yaw(yaw_to_set, speed = 0):
    try: 
        error = auv.get_yaw() - yaw_to_set 
        error = to_180(error)
        output = keep_yaw.regulator.process(error)
        output = clamp(output, 100, -100)
#        auv.set_motor_power(0, clamp((speed - output), 100, -100))#симулятор
#        auv.set_motor_power(1, clamp((speed + output), 100, -100))#симулятор
        
        if speed != 0:
            auv.set_motor_power(1, clamp(output + speed, 100, -100)) #Робот
            auv.set_motor_power(2, clamp(-output + speed, 100, -100)) #Робот
        else:
            auv.set_motor_power(1, output) #Робот
            auv.set_motor_power(2, -output) #Робот
        
        
    except AttributeError:
        keep_yaw.regulator = PD()
        keep_yaw.regulator.set_p_gain(1) # 0.8
        keep_yaw.regulator.set_d_gain(1) # 0.5

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

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
#    print('Круг: ', img_hsv[200, 480])
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
#    cv2.imshow('mask', img_mask)
#    cv2.imshow('hsv', img_hsv)
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def turn_by_line(img):
    contours = find_contours(img, color_orange)

    angle = 0

    if contours:
        # Вычисляем площадь для каждого контура, а затем берём контур с наибольшей
        # площадью, но только если он совпадает с искомой фигурой.
        areas = [
            cv2.contourArea(cnt) if (detect_shape(img, cnt) == 'rectangle') else 0 for cnt in contours
        ]

        if (len(areas) > 0) and (max(areas) > 500):
            cnt = contours[np.argmax(areas)]

            angle = calc_angle(img, cnt)

            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(img, 'angle: %d' % angle, (5, 30), font, 1, (255,255,255), 1, cv2.LINE_AA)
    
    # Стандартный способ
    if IS_AUV:
        power = max(min(angle * 0.75, 50), -50)
        auv.set_motor_power(1, power)
        auv.set_motor_power(2, -power)

    # Способ с использованием дополнительных условий увеличивающих точность поворота
#    if IS_AUV:
#        power = max(min(angle * 0.75, 50), -50)
#        if -7<=angle<=7:
#            power = max(min(angle, 50), -50) # Число, которое мы получим экспериментальным путем (при котором робот будет крутиться достаточно медленно)
#            auv.set_motor_power(1, power+10)
#            auv.set_motor_power(2, -power+10)
#        else:
#            auv.set_motor_power(1, power)
#            auv.set_motor_power(2, -power)

def find_max_coords(img, contours):
    areas = [
        cv2.contourArea(cnt1) if (detect_shape(img, cnt1) == 'rectangle') else 0 for cnt1 in contours
    ]
    
#    contours1 = [
#        cnt1 if (detect_shape(cnt1) == 'rectangle') else 0 for cnt1 in contours
#    ]

    if (len(areas) > 0):
        cnt2 = contours[np.argmax(areas)]
#        print(cnt2)
        rectangle = cv2.minAreaRect(cnt2)
        box = cv2.boxPoints(rectangle)
        box = np.int0(box)

        return box, cnt2

def img_process(num, img, cnt):
    font = cv2.FONT_HERSHEY_PLAIN
            # (circle_x, circle_y), circle_radius = cv2.minEnclosingCircle(contour)
            # circle_area = circle_radius ** 2 * math.pi
            # cv2.circle(img, (int(circle_x), int(circle_y)), int(circle_radius), (0,0, 255), 2, cv2.LINE_AA)
    rectangle = cv2.minAreaRect(cnt)
    box = np.int0(cv2.boxPoints(rectangle))
    cv2.drawContours(img,[box],0,(0,0,250),2)

    cv2.putText(img, 'Camera {}'.format(num), (5,25), font, 2, (255,255,255), 2, cv2.LINE_AA)

    return img

def rotate(depth, yaw):
    now = time.time()
    while time.time() - now < 1:
        keep_yaw(to_180(yaw+120))
        keep_depth(depth - 0.1)
        time.sleep(0.01)
    
    now = time.time()
    while time.time() - now < 1:
        keep_yaw(to_180(yaw+240))
        keep_depth(depth - 0.1)
        time.sleep(0.01)
    
    now = time.time()
    while time.time() - now < 1:
        keep_yaw(to_180(yaw+360))
        keep_depth(depth - 0.1)
        time.sleep(0.01)

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
            # cv2.circle(img, (int(circle_x), int(circle_y)), int(circle_radius), line_color, 2, cv2.LINE_AA)
            circles += 1

        if (shape_name == 'rect' or shape_name == 'square') and (shape == 'rect' or shape == 'square'):
            # cv2.drawContours(img, [box], 0, line_color, 2, cv2.LINE_AA)
            rect += 1
        # cv2.imshow('frame', img)
        # cv2.waitKey(30)
    if shape == 'rect':
        return rect
    else:
        return circles

def int_r(num):
    num = int(num + (0.5 if num > 0 else -0.5))
    return num

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
    video2 = cv2.VideoCapture(1)

    yaw = auv.get_yaw()

    color_orange = (
        (0, 0, 0),
        (90, 135, 150)
    )

    color_black = (
        (0, 0, 0),
        (180, 255, 90)
    )

#    rotate(0.3 + 0.1, yaw)
    depth = 0.4
    move_time = 0
    
    now = time.time()
    while time.time() - now < 3:
        keep_depth(depth + 0.1)
        keep_yaw(to_180(yaw))
        time.sleep(0.01)
        
    counter = 1
    circles = {}
    while counter < 2:
        prev_box = []
        # На случай если линии кривые, то мы будем каждый раз выравниваться по ним, дабы не сойти с курса
        # now = time.time()
        # while time.time() - now < 3:
        #     _, frame2 = video2.read()
        #     drawing = frame2.copy()
        #     mur_view.show(drawing, 1)
        #     turn_by_line(drawing)
        #     time.sleep(0.01)
        # yaw = auv.get_yaw()
        
#        time.sleep(0.1)

        now = time.time()
        while time.time() - now < 3:
            _, frame2 = video2.read()
            mur_view.show(frame2, 1)
        
        # Плывем вперед пока не наткнемся на оранжевую линию больше текущей
        while True:
            time1 = time.perf_counter()
#            print("swimming")
            _, frame2 = video2.read()

            # contours = find_contours(frame2[height/3:(2*height/3) + 1], color_orange) # Берем центральную треть изображения
            # contours = find_contours(frame2[:(height/2) + 1], color_orange) # Берем верхнюю половину изображения
            # contours = find_contours(frame2[height/2:], color_orange) # Берем нижнюю половину изображения

            contours = find_contours(frame2, color_orange)
            box, cnt = find_max_coords(frame2, contours)
            
            keep_yaw(to_180(yaw), -40)
            keep_depth(depth + 0.1)
            time.sleep(0.01)

            mur_view.show(img_process(1, frame2, cnt), 1)

            if prev_box != []:
                print(abs(box[0][1] - prev_box[0][1]))
                if abs(box[0][1] - prev_box[0][1]) > 50:
                    time2 = time.perf_counter()
                    move_time += (time2 - time1)
                    prev_box = box
                    break
            prev_box = box
        
        now = time.time()
        while time.time() - now < 3:
#            print('rotating 1')
            mur_view.show(frame2, 1)
            keep_yaw(to_180(yaw+90))
            keep_depth(depth + 0.1)
            time.sleep(0.01)
 
        circle = 0
        rect = 0
        frame = 0
        while True:
            print('reading circles')

            now = time.time()
            while time.time()-now < 1:
                _, frame1 = video1.read()
                _, frame2 = video2.read()

                mur_view.show(frame1, 0) # ДЛЯ РОБОТА
                mur_view.show(frame2, 1) # ДЛЯ РОБОТА
                
                keep_yaw(to_180(yaw+90)) # Поворот налево
                keep_depth(depth + 0.1)
                circle += search("circle", color_black, frame1)
#                rect += search("rect", color_black, frame1)
                frame += 1
                time.sleep(0.01)
            circles[counter] = int_r(circle/frame)
            LED(circles[counter], (255, 0, 0))
            print('Нашел ', circles[counter], ' черных кругов')
#            print('Нашел ', int_r(rect/frame), ' черных квадратов')
            break
        
        now = time.time()
        while time.time() - now < 3:
#            print('rotating 2')
            mur_view.show(frame2, 1)
            keep_yaw(to_180(yaw))
            keep_depth(depth + 0.1)
            time.sleep(0.01)
        counter += 1
    print("done")
    
    

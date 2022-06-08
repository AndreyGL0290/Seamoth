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

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def img_process(num, img, cnt):
    font = cv2.FONT_HERSHEY_PLAIN
            # (circle_x, circle_y), circle_radius = cv2.minEnclosingCircle(contour)
            # circle_area = circle_radius ** 2 * math.pi
            # cv2.circle(img, (int(circle_x), int(circle_y)), int(circle_radius), (0,0, 255), 2, cv2.LINE_AA)
    rectangle = cv2.minAreaRect(cnt)
    box = np.int0(cv2.boxPoints(rectangle))
    cv2.drawContours(img,[box],0,(0,0,250),2)

    cv2.putText(img,'Camera {}'.format(num),(5,25),font,2,(255,255,255),2,cv2.LINE_AA)

    return img

def detect_shape(cnt, drawing=None):
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

def find_max_coords(contours):
    areas = [
        cv2.contourArea(cnt1) if (detect_shape(cnt1) == 'rectangle') else 0 for cnt1 in contours
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
    power = max(min((y-middle) * 0.4, 50), -50)
    return power

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

def turn_by_line(img):
    contours = find_contours(img, color_orange)

    angle = 0

    if contours:
        # Вычисляем площадь для каждого контура, а затем берём контур с наибольшей
        # площадью, но только если он совпадает с искомой фигурой.
        areas = [
            cv2.contourArea(cnt) if (detect_shape(cnt, img) == 'rectangle') else 0 for cnt in contours
        ]

        if (len(areas) > 0) and (max(areas) > 500):
            cnt = contours[np.argmax(areas)]

            angle = calc_angle(img, cnt)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(img, 'angle: %d' % angle, (5, 30), font, 1, (255,255,255), 1, cv2.LINE_AA)
    # Стандартный способ
    if IS_AUV:
        power = max(min(angle * 0.75, 50), -50)
        # power = -power
        auv.set_motor_power(1, power)
        auv.set_motor_power(2, -power)

    # Способ с использованием дополнительных условий увеличивающих точность поворота
    # if IS_AUV:
    #     power = max(min(angle * 0.75, 50), -50)
    #     if -7<=angle<=7:
    #         power = max(min(angle, 50), -50) # Число, которое мы получим экспериментальным путем (при котором робот будет крутиться достаточно медленно)
    #         auv.set_motor_power(1, power+10)
    #         auv.set_motor_power(2, -power-10)
    #     else:
    #         auv.set_motor_power(1, power)
    #         auv.set_motor_power(2, -power)

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
        
        # line_color = (0,0,255)
        
        # Нарисуем соответствующую описанную фигуру вокруг контура

        if shape_name == 'circle':
            # cv2.circle(img, (int(circle_x), int(circle_y)), int(circle_radius), line_color, 2, cv2.LINE_AA)
            circles += 1

        if (shape_name == 'rect' or shape_name == 'square'):
            # cv2.drawContours(img, [box], 0, line_color, 2, cv2.LINE_AA)
            rect += 1
        # cv2.imshow('frame', img)
        # cv2.waitKey(30)
    return circles, rect

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

def keep_yaw(yaw_to_set, speed = 0):
    try:
        yaw_to_set += 10
        error = auv.get_yaw() - yaw_to_set 
        error = to_180(error)
        output = keep_yaw.regulator.process(error)
        output = clamp(output, 25, -25)
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

if __name__ == "__main__":
    video1 = cv2.VideoCapture(0)
    video2 = cv2.VideoCapture(1)
    
    height = len(video1.read()[1]) # Высота изображения
    width = len(video1.read()[1][1]) # Широта изображеия

    color_orange = (
        (0, 0, 0),
        (82, 255, 255)
    )

    color_black = (
        (0, 0, 0),
        (180, 255, 90)
    )

    depth = 0.5

    # Выравниваемся
    now = time.time()
    while time.time() - now < 3:
        _, frame2 = video2.read()
        drawing = frame2.copy()
        
        turn_by_line(drawing)
        
        mur_view.show(drawing, 1)
        time.sleep(0.01)
    yaw = auv.get_yaw()

    # Погружаемся и заодно смотрим цвета
    now = time.time()
    while time.time() - now < 5:
        _, frame2 = video2.read()
        mur_view.show(frame2, 1)
        keep_depth(depth + 0.1)
        keep_yaw(yaw)
        time.sleep(0.01)

    circles = {}
    move_time = 0
    counter = 1
    while counter < 4:
        prev_box = [] # Опустошаем массив
        while True:
            time1 = time.perf_counter()
            # print("swimming")
            _, frame2 = video2.read()

            contours = find_contours(frame2, color_orange)
            box, cnt = find_max_coords(contours)
            
            keep_yaw(to_180(yaw), -30) # Движение и выравнивание
            keep_depth(depth + 0.1)
            time.sleep(0.01)

            mur_view.show(img_process(1, frame2, cnt), 1)

            if prev_box != []:
                if abs(box[0][1] - prev_box[0][1]) > 50:
                    up = (7 * len(frame2)) // 16
                    down = (9 * len(frame2)) // 16

                    time2 = time.perf_counter()

                    now = time.time()
                    print('Нашел оранжевый')
                    while time.time() - now < 4:
                        _, frame2 = video2.read()
                        cnt = find_contours(frame2, color_orange)
                        keep_depth(depth + 0.1)
                        try:
                            center_point = get_center(frame2, cnt)
                            power = stabilization(center_point, up, down)
                            keep_yaw(to_180(yaw), power)
                        except ValueError:
                            print('Не вижу заданного цвета')
                            keep_yaw(to_180(yaw))
                        mur_view.show(frame2, 1) # Изображение уже обработано функцией get_center
                    
                    move_time += (time2 - time1)
                    prev_box = box
                    break
            prev_box = box

        print(move_time)

        now = time.time()
        while time.time() - now < 5:
#            _, frame1 = video1.read()
            _, frame2 = video2.read()
#            mur_view.show(frame1, 0)
            mur_view.show(frame2, 1)
            keep_yaw(yaw+90)
            keep_depth(depth+0.1)
            time.sleep(0.1)

        # Читаем круги и мигаем световой лентой
        while True:
            _, frame1 = video1.read()
            circle, rect = search(color_black, frame1)
            print('Нашел ', circle + rect, ' черных кругов')
            circles[counter] = circle + rect
        
#            auv.set_motor_power(0, 0)
            auv.set_motor_power(1, 0)
            auv.set_motor_power(2, 0)
#            auv.set_motor_power(3, 0)
 
            LED(circles[counter], (255, 0, 0))
            break
        
        # Стабилизация
        up = (7 * len(frame2)) // 16
        down = (9 * len(frame2)) // 16
        now = time.time()
        while time.time() - now < 6:
            _, frame2 = video2.read()
            cnt = find_contours(frame2, color_orange)
            keep_depth(depth + 0.1)

            try:
                center_point = get_center(frame2, cnt)
                power = stabilization(center_point, up, down)
                keep_yaw(to_180(yaw + 90), power)
            except ValueError:
                print('Не вижу заданного цвета')
                keep_yaw(to_180(yaw + 90))
            mur_view.show(frame2, 1) # Изображение уже обработано функцией get_center

        now = time.time()
        while time.time() - now < 3:
            _, frame2 = video2.read()
            mur_view.show(frame2, 1)
            keep_yaw(yaw)
            keep_depth(depth+0.1)
            time.sleep(0.1)
        
        # Стабилизация курса по линии
        now = time.time()
        while time.time() - now < 3:
            _, frame2 = video2.read()
            drawing = frame2.copy()
            
            turn_by_line(drawing)
            
            mur_view.show(drawing, 1)
            time.sleep(0.01)
        yaw = auv.get_yaw()

    # Отключаем все движители
    auv.set_motor_power(0, 0)
    auv.set_motor_power(1, 0)
    auv.set_motor_power(2, 0)
    auv.set_motor_power(3, 0) 
            
            
            
            
            
            

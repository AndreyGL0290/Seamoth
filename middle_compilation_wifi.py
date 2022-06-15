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

# OpenCv2
def search(color, img):
    circles = 0
    rect = 0
    contours = find_contours(img, color)
    for cnt in contours:
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
        
        # Нарисуем соответствующую описанную фигуру вокруг контура

        if shape_name == 'circle':
            circles += 1

        if shape_name == 'rect' or shape_name == 'square':
            rect += 1
    return rect, circles

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def int_r(num):
    num = int(num + (0.5 if num > 0 else -0.5))
    return num

def LED():
    auv.set_off_delay(0.5)
    auv.set_on_delay(1)
    auv.set_rgb_color(0, 0, 255)

def DELED():
    auv.set_off_delay(0)
    auv.set_on_delay(1)
    auv.set_rgb_color(0, 255, 0)

def detect_shape(cnt, drawing = 0):
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
    
        if (shape_name == 'rectangle' or shape_name == 'square'):
            try:
                cv2.drawContours(drawing, [box], 0, line_color, 2, cv2.LINE_AA)
            except:
                pass
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
    if IS_AUV:
        power = max(min(angle*1.25, 20), -20) # HERE
        auv.set_motor_power(1, power)
        auv.set_motor_power(2, -power)

def find_max_coords(img, contours):
    areas = [
        cv2.contourArea(cnt1) if (detect_shape(cnt1) == 'rectangle') else 0 for cnt1 in contours
    ]

    if (len(areas) > 0):
        cnt2 = contours[np.argmax(areas)]
        rectangle = cv2.minAreaRect(cnt2)
        box = cv2.boxPoints(rectangle)
        box = np.int0(box)

        return box, cnt2

def img_process(num, img, cnt):
    font = cv2.FONT_HERSHEY_PLAIN
    rectangle = cv2.minAreaRect(cnt)
    box = np.int0(cv2.boxPoints(rectangle))
    cv2.drawContours(img,[box],0,(0,0,255),2)

    cv2.putText(img, 'Camera {}'.format(num), (5,25), font, 2, (255,255,255), 2, cv2.LINE_AA)

    return img

def get_center(img, contours):
    areas = [
        cv2.contourArea(cnt1) if (detect_shape(cnt1) == 'rectangle') else 0 for cnt1 in contours
    ]

    if (len(areas) > 0):
        cnt_max = contours[np.argmax(areas)]
        rectangle = cv2.minAreaRect(cnt_max)
        box = cv2.boxPoints(rectangle)
        box = np.int0(box)
        cv2.drawContours(img, [box], 0, (0, 0, 255), 2, cv2.LINE_AA)
        
        center_point = [(box[0, 0] + box[1, 0] + box[2, 0] + box[3, 0]) // 4, (box[0, 1] + box[1, 1] + box[2, 1] + box[3, 1]) // 4]
        cv2.circle(img, tuple(center_point), 3, (0, 255, 0), -1) #######################
        return center_point
    raise ValueError

def stabilization(pt, up, down):
    y = pt[1]
    middle = up + (abs(down - up)//2)
    power = max(min((y-middle) * 0.25, 20), -20)
    return power

def stab(up, down, yaw, depth):
    _, frame1 = video1.read()
    _, frame2 = video2.read()
    keep_depth(depth + m)
    cnt = find_contours(frame2, color_orange)
    try:
        center_point = get_center(frame2, cnt)
        power = stabilization(center_point, up, down)
        
        keep_yaw(to_180(yaw), power)
    except ValueError:
        keep_yaw(to_180(yaw))
    mur_view.show(frame2, 1)
    mur_view.show(frame1[:, width//6:5*width//6], 0)
    time.sleep(0.01)

def keep_yaw(yaw_to_set, speed = 0):
    try:
        yaw_to_set = to_180(yaw_to_set)
        error = auv.get_yaw() - yaw_to_set
        error = to_180(error)
        output = keep_yaw.regulator.process(error)
        output = clamp(output, 25, -25)

        if speed != 0:
            auv.set_motor_power(1, clamp(output + speed, 100, -100)) # Робот
            auv.set_motor_power(2, clamp(-output + speed, 100, -100)) # Робот
        else:
            auv.set_motor_power(1, output) # Робот
            auv.set_motor_power(2, -output) # Робот
    except AttributeError:
        keep_yaw.regulator = PD()
        keep_yaw.regulator.set_p_gain(1) # 0.8
        keep_yaw.regulator.set_d_gain(1) # 0.5

def touch(depth, yaw):
    # Поворачиваемся
    now = time.time()
    while time.time() - now < 3:
        keep_yaw(to_180(yaw+angle_rot))
        keep_depth(depth+m)
        time.sleep(0.01)

    # Подплываем и касаемся
    now = time.time()
    while time.time() - now < 5:
        keep_depth(depth+m)
        keep_yaw(to_180(yaw+angle_rot), -20)
        time.sleep(0.01)
    
    # Чуть чуть отплываем, чтоб линия попала в поле зрения
#    now = time.time()
#    while time.time() - now < 3:
#        keep_depth(depth+m)
#        keep_yaw(to_180(yaw+angle_rot), 20)
#        time.sleep(0.01)
    
    # Выравниваемся
    now = time.time()
    up = (7 * len(frame2)) // 16
    down = (9 * len(frame2)) // 16
    while time.time() - now < 7:
        stab(up, down, yaw+angle_rot, depth)

def rotate(depth, yaw):
    now = time.time()
    while time.time() - now < 3:
        keep_yaw(to_180(yaw+angle_rot))
        keep_depth(depth+m)
        time.sleep(0.01)
    
    for i in range(1, 4):
        now = time.time()
        while time.time() - now < 3:
            keep_yaw(to_180((yaw+angle_rot)+120*i))
            keep_depth(depth+m)
            time.sleep(0.01)

def keep_depth(depth):
    global prev_time, prev_high_diff
    current_time = int(round(time.time() * 1000))
    k = 300
    high_diff = auv.get_depth() - depth

    power_0 = 0
    power_3 = 0

    diff_value = 10 / (current_time - prev_time) * (high_diff - prev_high_diff)
    
    power_value = clamp(high_diff*k + diff_value, 40, -40)
    power_0 = power_value
    power_3 = power_value

#    print(power_0, power_3)
    
    auv.set_motor_power(0, power_0)
    auv.set_motor_power(3, power_3)

    prev_time = current_time
    prev_high_diff = high_diff

def find_min_max(d):
    min_val = 999
    max_val = 0
    for k, v in d.items():
        if v > max_val:
            max_val = v
            max_key = k
        if v < min_val:
            min_val = v
            min_key = k
    return max_key, min_key

if __name__ == '__main__':
    # Пин 0, 3 - Правый, левый передние
    # Пин 1, 2 - Правый, левый задние

    video1 = cv2.VideoCapture(0) # Нижняя
    video2 = cv2.VideoCapture(1) # Передняя

    height = len(video1.read()[1]) # Высота изображения
    width = len(video1.read()[1][1]) # Широта изображеия

    up = (7 * height) // 16
    down = (9 * height) // 16

    color_black = (
        (0, 0, 0),
        (180, 255, 70)
    )

    color_orange = (
        (0, 0, 0),
        (96, 255, 133)
    )

    color_white = (
        (20, 0, 0),
        (180, 255, 255)
    )
    
    color_red1 = (
        (0, 0, 0),
        (180, 200, 100)
    )
    color_red2 = (
        (108, 0, 0),
        (180, 255, 255)
    )

    t = 0
    m = 0.2
    counter = 1
    circles = {}

    angle_rot = 90
    
    # Выравниваемся
    now = time.time()
    while time.time() - now < 7:
        _, frame2 = video2.read()
        drawing = frame2.copy()
        
        turn_by_line(drawing)
        mur_view.show(drawing, 1)
        time.sleep(0.01)
    
    yaw = auv.get_yaw()
    # Поворачиваемся на круг
    now = time.time()
    while time.time() - now < 3:
        keep_yaw(to_180(yaw+angle_rot))
        time.sleep(0.01)

    # Погружение
    while True:
        _, frame1 = video1.read()  # ПЕРЕДНЯЯ
        show1 = frame1[height//3-30:2*height//3+30] # !!!!!!!!!!!!!!!!!!!!!
        # show1 = frame1[height//3-60:2*height//3+60]
        # show1 = frame1[:height//2]

        mur_view.show(frame1, 0) # ДЛЯ РОБОТА
        mur_view.show(show1, 1) # ДЛЯ РОБОТА

        keep_yaw(to_180(yaw+angle_rot))
        keep_depth(t)
        time.sleep(0.01)
        # print(search(color_red2, show1)[1])
        if search(color_red1, show1)[1] >= 1:
            print("found red circle")
            depth = auv.get_depth()
            break
        t += 0.01
    
    # Стабилизируемся
    now = time.time()
    while time.time() - now < 4:
        stab(up, down, yaw+angle_rot, depth)
    
    # Поворот обратно к линии
    now = time.time()
    while time.time() - now < 3:
        keep_yaw(to_180(yaw))
        keep_depth(depth + m)
        time.sleep(0.01)
    
    prev_box = []
    counter = 1
    circles = {}

    # Добавил небольшой простой, ОН НУЖЕН
    now = time.time()
    while time.time() - now < 2:
        _, frame2 = video2.read()
        mur_view.show(frame2, 1)
        keep_yaw(to_180(yaw))
        keep_depth(depth+m)
        time.sleep(0.01)
    
    # Начинаем плыть по линии и выполнять задания
    while counter < 5:
        prev_box = [] # Опустошаем массив

        # Плывем вперед пока не наткнемся на оранжевую линию больше текущей
        while True:
            _, frame2 = video2.read()

            contours = find_contours(frame2, color_orange)
            box, cnt = find_max_coords(frame2, contours)
            
            keep_yaw(to_180(yaw), -25)
            keep_depth(depth + m)
            time.sleep(0.01)

            mur_view.show(img_process(1, frame2, cnt), 1)

            if prev_box != []:
                if abs(box[0][1] - prev_box[0][1]) > 50:
                    now = time.time()
                    while time.time() - now < 5: # 3
                        stab(up, down, yaw, depth)
                    break
            prev_box = box

        # Поворачиваемся на круги
        now = time.time()
        while time.time() - now < 3:
            keep_yaw(to_180(yaw+angle_rot))
            keep_depth(depth+m)
            time.sleep(0.01)

        # Стабилизируемся
        now = time.time()
        while time.time() - now < 5:
            stab(up, down, yaw+angle_rot, depth)

        # Читаем круги и мигаем световой лентой
        while True:
            _, frame1 = video1.read()
#            rect, circle = search(color_black, frame1[:, width//6:5*width//6])
            rect, circle = search(color_black, frame1)
            print('Нашел ', circle, ' черных кругов')
            print('Нашел ', rect, ' черных квадратов')
            circles[counter] = circle + rect

            k = circles[counter]
            n = 1.5

            if circles[counter] == 1:
                k = 1
                n = 1

            LED()
            
            now = time.time()
            while time.time() - now < k * n:
                stab(up, down, yaw+angle_rot, depth)
            
            DELED()
            break
        
    #    Стабилизируемся
    #    now = time.time()
    #    while time.time() - now < 4:
    #        stab(up, down, yaw+angle_rot, depth)
        
        # Поворот обратно в сторону линий
        now = time.time()
        while time.time() - now < 3:
            keep_yaw(to_180(yaw))
            keep_depth(depth+m)
            time.sleep(0.01)

        # Стабилизируемся
        now = time.time()
        while time.time() - now < 4:
            stab(up, down, yaw, depth)

        # Выравниваемся
        now = time.time()
        while time.time() - now < 3:
            _, frame2 = video2.read()
            drawing = frame2.copy()
            keep_depth(depth + m)
            turn_by_line(drawing)
            mur_view.show(drawing, 1)
            time.sleep(0.01)
            
        yaw = auv.get_yaw()
        counter+=1

    print("coming back")
    
    position = list(circles.keys())[-1]

    key_max, key_min = find_min_max(circles)
    # print(key_min, key_max)
    to_do = {key_min: rotate, key_max: touch}

    first = key_min
    if key_min < key_max:
        first = key_max
    
    # Добавил небольшой простой, ОН НУЖЕН
    now = time.time()
    while time.time() - now < 2:
        _, frame2 = video2.read()
        mur_view.show(frame2, 1)
        stab(up, down, yaw, depth)
    
    counter = 0
    while counter < position - first: # Едем к ближайшей табличке с крайним значением
        # Едем вперед
        prev_box = []
        while True:
            _, frame2 = video2.read()

            contours = find_contours(frame2, color_orange)
            box, cnt = find_max_coords(frame2, contours)
            
            keep_yaw(to_180(yaw), 30)
            keep_depth(depth + m)
            time.sleep(0.01)

            mur_view.show(img_process(1, frame2, cnt), 1)

            if prev_box != []:
                if abs(box[0][1] - prev_box[0][1]) > 50:
                    now = time.time()
                    while time.time() - now < 2:
                        stab(up, down, yaw, depth)
                    break
            prev_box = box
        counter += 1
    
    # print(position - counter)
    to_do[first](depth, yaw)

    position = first
    second = key_max
    if second > key_min:
        second = key_min
    
    # Добавил небольшой простой, ОН НУЖЕН
    now = time.time()
    while time.time() - now < 2:
        _, frame2 = video2.read()
        mur_view.show(frame2, 1)
        stab(up, down, yaw, depth)
    
    counter = 0
    while counter < position - second: # Едем к следующей табличке с крайним значением
        # Едем вперед
        prev_box = []
        while True:
            _, frame2 = video2.read()

            contours = find_contours(frame2, color_orange)
            box, cnt = find_max_coords(frame2, contours)
            
            keep_yaw(to_180(yaw), 30)
            keep_depth(depth + m)
            time.sleep(0.01)

            mur_view.show(img_process(1, frame2, cnt), 1)

            if prev_box != []:
                if abs(box[0][1] - prev_box[0][1]) > 50:
                    now = time.time()
                    while time.time() - now < 2:
                        stab(up, down, yaw, depth)
                    break
            prev_box = box
        counter += 1
    
    # print(position - counter)
    to_do[second](depth, yaw)

    # Добавил небольшой простой, ОН НУЖЕН
    now = time.time()
    while time.time() - now < 2:
        _, frame2 = video2.read()
        mur_view.show(frame2, 1)
        stab(up, down, yaw, depth)
    
    position = second
    counter = 0
    while counter < position: # Едем в начало
        # Едем вперед
        prev_box = []
        while True:
            contours = find_contours(frame2, color_orange)
            box, cnt = find_max_coords(frame2, contours)
            
            keep_yaw(to_180(yaw), 30)
            keep_depth(depth + m)
            time.sleep(0.01)

            mur_view.show(img_process(1, frame2, cnt), 1)

            if prev_box != []:
                if abs(box[0][1] - prev_box[0][1]) > 50:
                    now = time.time()
                    while time.time() - now < 2:
                        stab(up, down, yaw, depth)
                    break
            prev_box = box
        counter += 1
    
    # Всплываем
    now = time.time()
    while time.time() - now < 7:
        keep_depth(0)
        keep_yaw(yaw)
        time.sleep(0.01)

    # End of the program
    auv.set_motor_power(0, 0)
    auv.set_motor_power(1, 0)
    auv.set_motor_power(2, 0)
    auv.set_motor_power(3, 0)
    
    # 1- ,2- ,3- ,4- ,5- 
    
    
    
    
    
    
    

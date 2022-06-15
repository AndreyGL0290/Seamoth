from videoserver import VideoServer
import pymurapi as mur
import numpy as np
import math
import time
import cv2

auv = mur.mur_init()

prev_time = 0
prev_high_diff = 0

def clamp(power, max, min):
    if power >= max:
        return max
    elif power < min:
        return min
    return power

def keep_depth(depth):
    global prev_time, prev_high_diff
    current_time = int(round(time.time() * 1000))
    k = 100
    high_diff = auv.get_depth() - depth

    power_0 = 0
    power_3 = 0

    diff_value = 10 / (current_time - prev_time) * (high_diff - prev_high_diff)
    
    power = clamp(high_diff*k + diff_value, 40, -40)
    print(power)

#    print(power_0, power_3)
    
    auv.set_motor_power(0, power)
    auv.set_motor_power(3, power)

    prev_time = current_time
    prev_high_diff = high_diff

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

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

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


if __name__ == '__main__':
    video1 = cv2.VideoCapture(0) # Нижняя
    video2 = cv2.VideoCapture(1) # Передняя

    height = len(video1.read()[1]) # Высота изображения
    width = len(video1.read()[1][1]) # Широта изображеия

    up = (7 * height) // 16
    down = (9 * height) // 16

    color_black = (
        (0, 0, 0),
        (180, 255, 113)
    )

    color_orange = (
        (0, 0, 0),
        (98, 255, 140)
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
        (0, 0, 0),
        (180, 180, 255)
    )
    yaw = auv.get_yaw()
    t = 0
    angle_rot = 90
    m = 0.3
    # Погружение
    while True:
        _, frame1 = video1.read()  # ПЕРЕДНЯЯ
        show1 = frame1[height//3-30:2*height//3+30]

        keep_yaw(to_180(yaw+angle_rot))
        keep_depth(t)
        time.sleep(0.01)
        # print(search(color_red2, show1)[1])
        if search(color_red1, show1)[1] >= 1:
            print("found red circle")
            depth = auv.get_depth()
            break
        t += 0.01
    
    now = time.time()
    while time.time() - now < 3:
        keep_yaw(yaw)
        keep_depth(depth + m)
        time.sleep(0.01)
    
    now = time.time()
    while time.time() - now < 3:
        keep_yaw(yaw, -30)
        keep_depth(depth + m)
        time.sleep(0.01)
    
    now = time.time()
    while time.time() - now < 7:
        keep_depth(depth + m)
        keep_yaw(yaw)
        time.sleep(0.01)
    
    now = time.time()
    while time.time() - now < 7:
        keep_depth(0)
        time.sleep(0.01)

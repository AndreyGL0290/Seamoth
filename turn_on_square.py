from videoserver import VideoServer
import pymurapi as mur
import numpy as np
import math
import time
import cv2

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
        error = auv.get_yaw() - to_180(yaw_to_set) 
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

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
    
    # img_layed = cv2.bitwise_and(img, img, mask=img_mask)
    # cv2.imshow('masked', img_layed)

    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

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

def get_center(img, contours):
    areas = [
        cv2.contourArea(cnt1) if (detect_shape(cnt1) == 'rectangle') else 0 for cnt1 in contours
    ]
    
#    contours1 = [
#        cnt1 if (detect_shape(cnt1) == 'rectangle') else 0 for cnt1 in contours
#    ]

    if (len(areas) > 0):
        cnt_max = contours[np.argmax(areas)]
        rectangle = cv2.minAreaRect(cnt_max)
        box = cv2.boxPoints(rectangle)
        box = np.int0(box)
        cv2.drawContours(img, [box], 0, (0, 0, 255), 2, cv2.LINE_AA)
        
        center_point = ((box[0, 0] + box[1, 0] + box[2, 0] + box[3, 0]) // 4, (box[0, 1] + box[1, 1] + box[2, 1] + box[3, 1]) // 4)

        cv2.circle(img, center_point, 3, (0, 255, 0), -1)
        return center_point
    raise ValueError

def search(shape, color, img):
    contours = find_contours(img, color)
    for cnt in contours:
        area = cv2.contourArea(cnt)

        if area < 300:
            continue

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
            'rect' if aspect_ratio > 1.25 else 'square': rectangle_area
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
        if (shape_name == 'rect' or shape_name == 'square') and (shape == 'rect' or shape == 'square'):
            cv2.drawContours(img, [box], 0, line_color, 2, cv2.LINE_AA)

def stabilization_Y(pt, up, down):
    y = pt[1]
    middle = up + (abs(down - up)//2)
    power = max(min((y-middle) * 0.4, 50), -50)
    return power

def stabilization_X(pt, up, down):
    x = pt[0]
    middle = up + (abs(down - up)//2)
    power = max(min((x-middle) * 0.4, 25), -25)
    return power

if __name__ == '__main__':
    video1 = cv2.VideoCapture(0)

    # video2 = cv2.VideoCapture(1)
    color_white = (
        (62, 0, 120),
        (84, 55, 255)
    )

    # Иммитация поворота
    time.sleep(3)
    
    # ДЛЯ РОБОТА
    # yaw = auv.get_yaw()
    # now = time.time()
    # while time.time() - now < 3:
    #     keep_yaw(yaw+90)
        # time.sleep(0.1)
    
    up = 7 * len(video1.read()[1][0]) // 16
    down = 9 * len(video1.read()[1][0]) // 16
    while True:
        _, frame1 = video1.read()
        cnt = find_contours(frame1, color_white)
        # kp = cv2.waitKey(30)
        # if kp == ord('q'):
        #     break
        try:
            center_point = get_center(frame1[:, len(frame1[0])//3:2*len(frame1[0])//3], cnt)
            power = stabilization_X(center_point, up, down)
            cv2.line(frame1, (up, 0), (up, len(frame1)), (0, 0, 255), 2)
            cv2.line(frame1, (down, 0), (down, len(frame1)), (0, 0, 255), 2)
#            cv2.imshow('frame1', frame1)
            key_pressed = cv2.waitKey(30)
            if key_pressed == ord('q'):
                break

            # Для робота
            auv.set_motor_power(1, -power)
            auv.set_motor_power(2, power)
        except ValueError:
            print('Заданный цвет не найден')
        mur_view.show(frame1[:, len(frame1[0])//3:2*len(frame1[0])//3], 0)
            

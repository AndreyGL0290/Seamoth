from videoserver import VideoServer
import pymurapi as mur
import numpy as np
import math
import time
import cv2

IS_AUV = False

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

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
#    print('Круг: ', img_hsv[200, 480])
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
#    cv2.imshow('mask', img_mask)
#    cv2.imshow('hsv', img_hsv)
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
    power = max(min((y-middle) * 0.25, 50), -50)
    return power

if __name__ == "__main__":
    video1 = cv2.VideoCapture(0)
    video2 = cv2.VideoCapture(1)
    
    height = len(video1.read()[1]) # Высота изображения
    width = len(video1.read()[1][1]) # Широта изображеия

    color_orange = (
        (0, 146, 49),
        (22, 255, 255)
    )

    yaw = auv.get_yaw()
    depth = 0.4

    # Погружаемся и заодно смотрим цвета
    now = time.time()
    while time.time() - now < 5:
        _, frame2 = video2.read()
        mur_view.show(frame2, 1)
        keep_depth(depth + 0.1)
        keep_yaw(yaw)
        time.sleep(0.01)
    
    move_time = 0
    counter = 0
    while counter < 5:
        prev_box = [] # Опустошаем массив
        while True:
            time1 = time.perf_counter()
            # print("swimming")
            _, frame2 = video2.read()

            contours = find_contours(frame2, color_orange)
            box, cnt = find_max_coords(contours)
            
            keep_yaw(to_180(yaw), -50) # Движение и выравнивание
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
                        try:
                            center_point = get_center(frame2, cnt)
                            power = stabilization(center_point, up, down)
                            
                            auv.set_motor_power(1, power)
                            auv.set_motor_power(2, power)
                        except ValueError:
                            print('Не вижу заданного цвета')
                        mur_view.show(frame2, 1) # Изображение уже обработано функцией get_center
                    
                    move_time += (time2 - time1)
                    prev_box = box
                    break
            prev_box = box
        print(move_time)
        now = time.time()
        while time.time() - now < 3:
            keep_yaw(yaw-90)
            keep_depth(depth+0.1)
            time.sleep(0.1)


        now = time.time()
        while time.time() - now < 3:
            keep_yaw(yaw)
            keep_depth(depth+0.1)
            time.sleep(0.1)

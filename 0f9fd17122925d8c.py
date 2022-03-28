import pymurapi as mur
import cv2
import numpy as np
import math
import time

auv = mur.mur_init()

p_time = 0
p_error = 0.0

prev_time = 0
prev_error = 0.0
def to_360(angle):
    if angle > 0.0:
        return angle
    if angle <= 0.0:
        return 360.0 + angle
        
def to_180(a):
    if a > 180.0:
        return a - 360
    if a < -180.0:
        return a + 360
    return a
    
def clamp(v, max_v, min_v):
    if v > max_v:
        return max_v
    if v < min_v:
        return min_v
    return v

def keep_depth(value):
    global p_time
    global p_error
    
    c_time = int(round(time.time() * 1000))
    
    error_depth = auv.get_depth() - value
    
    power_2 = 0
    power_3 = 0
    
    power_value = error_depth * 40
    diff_value = 5 / (c_time - p_time) * (error_depth - p_error)
    
    power_2 = clamp(power_value + diff_value, 100, -100)
    power_3 = clamp(power_value + diff_value, 100, -100)
    
    auv.set_motor_power(2, power_2)
    auv.set_motor_power(3, power_3)
    
    p_time = c_time
    p_error = error_depth

def keep_yaw(value):
    global prev_time
    global prev_error
    
    current_time = int(round(time.time() * 1000))
    
    error_yaw = auv.get_yaw() - value
    error_yaw = to_180(error_yaw)
    
    power_0 = 0
    power_1 = 0
    
    power_value = error_yaw * 0.35
    diff_value = 0.3 / (current_time - prev_time) * (error_yaw - prev_error)
    
    power_0 = clamp(power_value - diff_value, 100, -100)
    power_1 = clamp(power_value + diff_value, 100, -100)
    
    auv.set_motor_power(0, -power_0)
    auv.set_motor_power(1, power_1)
    
    prev_time = current_time
    prev_error = error_yaw
    return clamp(power_value - diff_value, 100, -100)

# OpenCv2
def search(shape, color, img):
    circles = 0
    rect = 0
    drawing = img.copy()
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
        
        line_color = (0,0,255)
        
        # Нарисуем соответствующую описанную фигуру вокруг контура

        if shape_name == 'circle' and shape == 'circle':
            # cv2.circle(drawing, (int(circle_x), int(circle_y)), int(circle_radius), line_color, 2, cv2.LINE_AA)
            circles += 1

        if (shape_name == 'rect' or shape_name == 'square') and (shape == 'rect' or shape == 'square'):
            # cv2.drawContours(drawing, [box], 0, line_color, 2, cv2.LINE_AA)
            rect += 1
        # cv2.imshow('drawing', drawing)
        # cv2.waitKey(30)
    if shape == 'rect':
        return rect
    else:
        return circles

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
#    print('Круг: ', img_hsv[200, 480])
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
#    cv2.imshow('mask', img_mask)
#    cv2.imshow('hsv', img_hsv)
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours
    
if __name__ == '__main__':
    now = time.time()
    
    color_black = (
        ( 0, 0,  0),
        ( 180, 255, 70)
    )

    color_orange = (
        ( 0, 140,  100),
        ( 20, 255, 255)
    )
        
    color_white = (
        (20, 0, 0),
        (180, 255, 255)
    )

    rotate_left = False
    rotate_right = False
    counter = 1
    circles = {}

    swim_straight = True
    search_for_orange = False

    video1 = cv2.VideoCapture(0) # ДЛЯ РОБОТА
    video2 = cv2.VideoCapture(1) # ДЛЯ РОБОТА
    
    _, img = video1.read() # ДЛЯ РОБОТА
    height = len(img) # ДЛЯ РОБОТА
    width = len(img[0]) # ДЛЯ РОБОТА

    # img = auv.get_image_bottom() # ДЛЯ СИМУЛЯТОРА
    # height = len(img) # ДЛЯ СИМУЛЯТОРА
    # width = len(img[0]) # ДЛЯ СИМУЛЯТОРА

    while True:
        keep_depth(0.7)
        time.sleep(0.03)
        _, img = video1.read() # ДЛЯ РОБОТА
        # img = auv.get_image_bottom() # ДЛЯ СИМУЛЯТОРА
        # cv2.imshow('orange', img[height-40:height])
        # cv2.imshow('white', img[height//2-20:height//2+20, width//2-20:width//2+20])
        # cv2.waitKey(30)
        # img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        if counter == 5:
            auv.set_motor_power(0, 0)
            auv.set_motor_power(1, 0)
            break

        # print(search('rect', color_orange, img[100:140, 140:180]), search_for_orange)
        if search('rect', color_orange, img[height-40:height]) >= 1 and search_for_orange:
            swim_straight = False
            search_for_orange = False
        # print(search('rect', color_white, img[height//2-20:height//2+20, width//2-20:width//2+20]), search('rect', color_orange, img[height//2-20:height//2+20, width//2-20:width//2+20]))
        if search('rect', color_white, img[height//2-20:height//2+20, width//2-20:width//2+20]) >= 1 and search('rect', color_orange, img[height//2-20:height//2+20, width//2-20:width//2+20]) == 0:
            swim_straight = True
            search_for_orange = True

        if auv.get_depth() < 0.75 and auv.get_depth() > 0.65 and swim_straight and not rotate_left and not rotate_right:
            keep_yaw(0)
            time.sleep(0.01)
            auv.set_motor_power(0, 25)
            auv.set_motor_power(1, 25)
        
        elif auv.get_depth() < 0.75 and auv.get_depth() > 0.65 and not rotate_left and not rotate_right:
            auv.set_motor_power(0, 0)
            auv.set_motor_power(1, 0)
            time.sleep(3)
            rotate_left = True
        
        elif auv.get_depth() < 0.75 and auv.get_depth() > 0.65 and rotate_left:
            power = keep_yaw(-90)
            time.sleep(0.01)
            if abs(power) < 1:
                rotate_left = False
                rotate_right = True
                # img2 = auv.get_image_front() # ДЛЯ СИМУЛЯТОРА
                _, img2 = video2.read() # ДЛЯ РОБОТА
                circles[counter] = search('circle', color_black, img2)
                counter += 1

        elif auv.get_depth() < 0.75 and auv.get_depth() > 0.65 and rotate_right:
            power = keep_yaw(0)
            time.sleep(0.01)
            if abs(power) < 1:
                rotate_left = False
                rotate_right = False
                swim_straight = True
    print(circles)

    # Начинаем новый цикл, в котором будем возращаться назад
    # while True:
    #     pass # Тут код

    
#            if search('rect', color_orange, img[120:160, 140:180]) >= 1: 
#                auv.set_motor_power(0, 0)
#                auv.set_motor_power(1, 0)
#                keep_yaw(-90)                
#                time.sleep(0.01)
#                
#                img2 = auv.get_image_front()
#                print(search('circle', color_black, img2))
#                
#                if (time.time() - now) > 10: 
#                    keep_yaw(0)
#                    time.sleep(0.01)
                    
                
                
#            if (time.time() - now) > 15:
#                auv.set_motor_power(0, 0)
#                auv.set_motor_power(1, 0)
#                break
#    time.sleep(4)
#    now2 = time.time()
#    while True:
#        keep_depth(0.7)
#        time.sleep(0.03)
#        keep_yaw(180)
#        time.sleep(0.01)
#        if (time.time() - now2) > 8 and (time.time() - now2) < 19: 
#            auv.set_motor_power(0, 50)
#            auv.set_motor_power(1, 50)
#            time.sleep(0.1)
#        if (time.time() - now2) > 22:
#            break   
#    time.sleep(4)
#    now3 = time.time()
#    while True:
#        keep_depth(0.7)
#        time.sleep(0.03)
#        keep_yaw(0)
#        time.sleep(0.01)  
#        if (time.time() - now3) > 5 and (time.time() - now3) < 7.5: 
#            auv.set_motor_power(0, 50)
#            auv.set_motor_power(1, 50)
#            time.sleep(0.1)
        
#        while True:
#            
#            keep_yaw(90)
#            time.sleep(0.5)
#            
#            auv.set_motor_power(0, 50)
#            auv.set_motor_power(1, 50)
#            time.sleep(0.1)
            
#Свет лента
#auv.set_on_delay(1)
#    auv.set_off_delay(0.5)
#    # Зеленый
#    auv.set_rgb_color(225, 0, 225)
#    time.sleep(6)

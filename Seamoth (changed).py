import pymurapi as mur
import cv2
import numpy as np
import math
import time
from videoserver import VideoServer # ДЛЯ РОБОТА

auv = mur.mur_init()

mur_view = VideoServer() # ДЛЯ РОБОТА

p_time = 0
p_error = 0.0

prev_time = 0
prev_high_diff = 0.0
prev_error = 0.0

def to_180(a):
    if a > 180.0:
        return a - 360
    if a < -180.0:
        return a + 360
    return a
    
def clamp(v, max, min):
    if v > max:
        return max
    if v < min:
        return min
    return v
    
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
    if abs(high_diff) < 0.2:
        k = 200
    power_value = clamp(high_diff*k + diff_value, 100, -100)
    power_0 = power_value
    power_3 = power_value
    
    print(power_0, power_3)
    
    auv.set_motor_power(0, power_0)
    auv.set_motor_power(3, power_3)

    prev_time = current_time
    prev_high_diff = high_diff
        
def keep_yaw(yaw_to_set, speed):
    try: 
        error = auv.get_yaw() - yaw_to_set 
        error = to_180(error)
        output = keep_yaw.regulator.process(error)
        output = clamp(output, 100, -100)
#        auv.set_motor_power(0, clamp((speed - output), 100, -100))#симулятор
#        auv.set_motor_power(1, clamp((speed + output), 100, -100))#симулятор
        
        auv.set_motor_power(2, clamp((speed - output), 100, -100))#робот
        auv.set_motor_power(1, clamp((speed + output), 100, -100))#робот
        
        
    except AttributeError:
        keep_yaw.regulator = PD()
        keep_yaw.regulator.set_p_gain(1) # 0.8
        keep_yaw.regulator.set_d_gain(1) # 0.5
        

# OpenCv2
def search(shape, color, img):
    circles = 0
    rect = 0
    # drawing = img.copy()
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

def find_contours(img, color):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
#    print('Круг: ', img_hsv[200, 480])
    img_mask = cv2.inRange(img_hsv, color[0], color[1])
#    cv2.imshow('mask', img_mask)
#    cv2.imshow('hsv', img_hsv)
    contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def img_process(num, img, color):
    font = cv2.FONT_HERSHEY_PLAIN
    contours = find_contours(img, color)

    if contours:
        for contour in contours:
            if cv2.contourArea(contour) > 200:
                (circle_x, circle_y), circle_radius = cv2.minEnclosingCircle(contour)
                circle_area = circle_radius ** 2 * math.pi
                cv2.circle(img, (int(circle_x), int(circle_y)), int(circle_radius), (0,0, 255), 2, cv2.LINE_AA)
#                rectangle = cv2.minAreaRect(contour)
#                box = np.int0(cv2.boxPoints(rectangle))
#                cv2.drawContours(img,[box],0,(0,0,250),2)

    cv2.putText(img,'Camera {}'.format(num),(5,25),font,2,(255,255,255),2,cv2.LINE_AA)

    return img

def circles_correction(depth, yaw):
    # Если сверху по центру изображения белые пиксели, то всплываем чуть чуть
    _, frame1 = video1.read()  # ПЕРЕДНЯЯ
    _, frame2 = video2.read()  # НИЖНЯЯ
    while search("rect", ((0,0,114), (90, 108, 255)), frame1[:15, width//2-40:width//2+40]) and search("rect", ((0,0,114), (90, 108, 255)), frame1[height-15:, width//2-40:width//2+40]):
        _, frame1 = video1.read()  # ПЕРЕДНЯЯ
        _, frame2 = video2.read()  # НИЖНЯЯ
        keep_depth(depth)
        keep_yaw(yaw, 0)
        time.sleep(0.01)
        if search("rect", ((0,0,114), (90, 108, 255)), frame1[:15, width//2-40:width//2+40]):
            depth += 0.01
        if search("rect", ((0,0,114), (90, 108, 255)), frame1[height-15:, width//2-40:width//2+40]):
            depth -+ 0.01
        print("Выравниваю картинку, текущая глубина: ", depth)
    return depth

def int_r(num):
    num = int(num + (0.5 if num > 0 else -0.5))
    return num

def touch():
    now = time.time()
    while time.time()-now<=3:
        keep_yaw(to_180(yaw), 0)
        keep_depth(k)
        time.sleep(0.01)
    
    now = time.time()
    while time.time()-now<=3:
        keep_yaw(to_180(yaw), -15)
        keep_depth(k)
        time.sleep(0.01)
    
    now = time.time()
    while time.time()-now<=3:
        keep_yaw(to_180(yaw), 10)
        keep_depth(k)
        time.sleep(0.01)
    
    while time.time()-now<=3:
        keep_yaw(to_180(yaw+angle), 0)
        keep_depth(k)
        time.sleep(0.01)
    print("touched")

def LED(times, color):
    auv.set_on_delay(1)
    auv.set_off_delay(0.5)
    auv.set_rgb_color(color[0], color[1], color[2])
    if times == 1:
        time.sleep(times)
    time.sleep(times*1.5)
    auv.set_off_delay(0)
    auv.set_rgb_color(0, 255, 0)
    
def rotate():
    now = time.time()
    while time.time()-now<=3:
        keep_yaw(to_180(yaw+200), -10)
        keep_depth(k)
        time.sleep(0.01)
    
    now = time.time()
    while time.time()-now<=3:
        keep_yaw(to_180(yaw), -10)
        keep_depth(k)
        time.sleep(0.01)
    
    now = time.time()
    while time.time()-now<=3:
        keep_yaw(to_180(yaw+angle), -10)
        keep_depth(k)
        time.sleep(0.01)
        
if __name__ == '__main__':
    video1 = cv2.VideoCapture(0) # Нижняя
    video2 = cv2.VideoCapture(1) # Передняя

    height = len(video1.read()[1]) # Высота изображения
    width = len(video1.read()[1][1]) # Широта изображеия

    color_black = (
        (104, 0, 0),
        (180, 255, 107)
    )

    color_orange = (
        (0, 0, 0),
        (100, 253, 105)
    )

    color_white = (
        (20, 0, 0),
        (180, 255, 255)
    )
    
    color_red = (
        (0, 0, 0),
        (180, 118, 255)
    )

#    while True:
#        _, frame1 = video1.read()  # ПЕРЕДНЯЯ
#        _, frame2 = video2.read()  # НИЖНЯЯ
#        circles = search("circle", color_black, frame1)
#        print(circles)
#        auv.set_on_delay(1)
#        auv.set_off_delay(0.5)
#        auv.set_rgb_color(0, 0, 255)
#        time.sleep(circles*1.5)
#        if circles != 0:
#            break                                 # СВЕТОВАЯ ЛЕНТА
#    auv.set_off_delay(0)
#    auv.set_rgb_color(0, 255, 0)

    k = 0.1
    counter = 1
    circles = {}
    yaw = auv.get_yaw()
    angle = 130
#    while True:
#        _, frame1 = video1.read()
##       mur_view.show(img_process(0, frame1, color_red), 0)
##       mur_view.show(img_process(1, frame1, color_orange), 1)
##       mur_view.show(img_process(1, frame1, color_black), 1)
#        while (time.time()-now) <= 2:
#            keep_yaw(yaw+angle, 0) # Поворот налево
#            time.sleep(0.01)
#        break
    
#     Погружение в воду до красного круга
    while True:
        _, frame1 = video1.read()  # ПЕРЕДНЯЯ
        _, frame2 = video2.read()  # НИЖНЯЯ
        mur_view.show(img_process(0, frame1, color_black), 0) # ДЛЯ РОБОТА
        mur_view.show(img_process(1, frame2, color_orange), 1) # ДЛЯ РОБОТА
        keep_yaw(to_180(yaw), 0)
        keep_depth(k)
        time.sleep(0.01)
        #      print(search('circle', color_red, frame1))
        if search('circle', color_red, frame1) >= 1:
            print("found red circle")
            depth = auv.get_depth()
            break
        k += 0.01
    while True:
        print('depthing')
        keep_depth(depth + 0.1)
        time.sleep(0.01)
## Минусы на плюсы
#    #    Поворот и считывание кругов по линии
#    while counter != 5:
#        print(counter)
#        frame = 0
#        circle = 0
#        while True:
#            if counter == 1:
#                break
#            _, frame1 = video1.read()  # ПЕРЕДНЯЯ
#            _, frame2 = video2.read()  # НИЖНЯЯ
#            keep_yaw(to_180(yaw+angle), -30) # Плывем прямо
#            keep_depth(k)
#            time.sleep(0.01)
#            # Ищет оранжевый
#            if search('rect', color_orange, frame2[height//2:]):
#                print('Нашел оранжевый')
#                LED(1, (239, 114, 21))
##                 now = time.time()
#   #              while (time.time()-now) < 1.5:
#   #                 keep_yaw(yaw+85, -30)
#   #                 time.sleep(0.01)
#   #                 print("fffff")
#   #             break
#                break
      
        # while True:
        #     if counter == 1:
        #         break
        #     _, frame1 = video1.read()  # ПЕРЕДНЯЯ
        #     _, frame2 = video2.read()  # НИЖНЯЯ
              
        #     keep_yaw(yaw, 0) # Поворот налево
        #     time.sleep(0.01)
        #     now = time.time()
        #     while (time.time()-now) <= 2:
        #         keep_yaw(yaw, 0) # Поворот налево
        #         time.sleep(0.01)
        #     break
#            if auv.get_yaw() <= to_180(yaw+5) and auv.get_yaw() >= to_180(yaw-5):
#                print("Повернул налево")
#                break
      
        # while True:
        # # Код для черных кругов
        #     if counter == 1:
        #         break
        #     _, frame1 = video1.read()
        #     _, frame2 = video2.read()
            
        #     mur_view.show(img_process(1, frame2, color_orange), 1) # ДЛЯ РОБОТА
        #     now = time.time()
        #     while (time.time()-now) <= 2:
        #         keep_yaw(yaw, 0) # Поворот налево
        #         time.sleep(0.01)
            
        #     now = time.time()
        #     while (time.time()-now) <= 3:
        #         keep_yaw(yaw, 0) # Поворот налево
        #         circle += search("circle", color_black, frame1)
        #         frame += 1
        #         time.sleep(0.01)
        #     counter += 1
        #     circles[counter] = int_r(circle/frame)
        #     auv.set_on_delay(1)
        #     auv.set_off_delay(0.5)
        #     auv.set_rgb_color(255, 0, 125)
        #     time.sleep(circles[counter]*1.5)
        #     auv.set_off_delay(0)
        #     auv.set_rgb_color(0, 255, 0)
        #     print('Нашел ', circles[counter], ' черных кругов')
        #     if circles[counter] == 1:
        #    #                while True:
        #    #                    keep_yaw(to_180(yaw-90))
        #    #                    if to_180(yaw-95) <= auv.get_yaw() <= to_180(yaw-85):
        #    #                        break
        #    #                while True:
        #    #                    keep_yaw(to_180(yaw-180))
        #    #                    if to_180(yaw-185) <= auv.get_yaw() <= to_180(yaw-175):
        #    #                        break
        #    #                while True:
        #    #                    keep_yaw(to_180(yaw-270))
        #    #                    if to_180(yaw-275) <= auv.get_yaw() <= to_180(yaw-265):
        #    #                        break
        #         while True:
        #             now = time.time()
        #             while (time.time()-now) <= 3:
        #                 keep_yaw(to_180(yaw-190), 0) # Поворот налево
        #                 time.sleep(0.01)
        #             break
        #         while True:
        #             now = time.time()
        #             while (time.time()-now) <= 3:
        #                 keep_yaw(yaw, 0) # Поворот налево
        #                 time.sleep(0.01)
        #             break
        #     break
   
       
#        while True:
#            if counter == 1:
#                counter += 1
#        #             print("hhh")
#            _, frame1 = video1.read()  # ПЕРЕДНЯЯ
#            _, frame2 = video2.read()  # НИЖНЯЯ
#            keep_depth(k)
#            time.sleep(0.01)
#            now = time.time()
#            while (time.time()-now) <= 3:
#                keep_yaw(to_180(yaw+angle), 0) # Поворот налево
#                time.sleep(0.01)
#            break
#            # if to_180(yaw+angle-1) <= auv.get_yaw() <= to_180(yaw+angle+1):
#            #    print('Повернул')
#            #    break
#       
#        while True:
#        #            print('fghgh')
#            _, frame1 = video1.read()  # ПЕРЕДНЯЯ
#            _, frame2 = video2.read()  # НИЖНЯЯ
#            keep_yaw(to_180(yaw+angle), -30) # Плывем прямо
#            keep_depth(k)
#            time.sleep(0.01)
#            mur_view.show(img_process(1, frame2, color_orange), 1) # ДЛЯ РОБОТА
#            print(search("rect", color_orange, frame2[height//1.5:]))
#            if search('rect', color_orange, frame2[height//1.5:]) == 0:
#                print('Нашел НЕ оранжевый')
#                # LED(2, (239, 114, 21))
##                 now = time.time()
##                 while (time.time()-now) < 0.5:
##                     keep_yaw(yaw+90, -30)
##                     time.sleep(0.01)
##                     print("fffff")
#                break

    # line_number = 6
    # while line_number != 1:
    #     while True:
    #         # Разворот
    #         keep_yaw(to_180(yaw-angle), 0)
    #         keep_depth(k)
    #         time.sleep(0.01)
    #         now = time.time()
    #         while (time.time()-now) <= 3:
    #             keep_yaw(to_180(yaw+angle), 0) # Поворот налево
    #             time.sleep(0.01)
    #         break
    #     while True:
    #         keep_yaw(to_180(yaw-angle), -30)
    #         keep_depth(k)
    #         time.sleep(0.01)
    #         _, frame1 = video1.read()  # ПЕРЕДНЯЯ
    #         _, frame2 = video2.read()  # НИЖНЯЯ
    #         # Ищет оранжевый
    #         if search('rect', color_orange, frame2[height//2:]):
    #             line_number -= 1
    #             break
    #     while True:
    #         _, frame1 = video1.read()  # ПЕРЕДНЯЯ
    #         _, frame2 = video2.read()  # НИЖНЯЯ
    #         keep_yaw(to_180(yaw-angle), -30) # Плывем прямо
    #         keep_depth(k)
    #         time.sleep(0.01)
    #         if search('rect', color_orange, frame2[height//2:]) == 0:
    #             print('Нашел НЕ оранжевый')
    #             break
       
    # while k>=0:
    #     # Всплываем
    #     keep_depth(k)
    #     k-=0.01
#        

    # Плывем вперед по времени
    # now = time.time()
    # angle = 90
#    Повернули
#    while time.time()-now<=3:
#        keep_yaw(to_180(yaw+angle), 0)
#        keep_depth(k)
#        time.sleep(0.01)        
##    Проплыли
#
#    now = time.time()
#    while time.time()-now<=3:
#        keep_yaw(to_180(yaw+angle), -50)
#        keep_depth(k)
#        time.sleep(0.01)
##    повернули обратно
#    now = time.time()
#    while time.time()-now<=3:
#        keep_yaw(to_180(yaw), 0)
#        keep_depth(k)
#        time.sleep(0.01)
##    помигали
#    _, frame1 = video1.read()  # ПЕРЕДНЯЯ
#    _, frame2 = video2.read()  # НИЖНЯЯ
#    auv.set_on_delay(1)
#    auv.set_off_delay(0.5)
#    auv.set_rgb_color(0, 0, 255)
#    time.sleep(4*1.5)
#    auv.set_off_delay(0)
#    auv.set_rgb_color(0, 255, 0)
#    
#    # Повернули
#    now = time.time()
#    while time.time()-now<=3:
#        keep_yaw(to_180(yaw+angle), 0)
#        keep_depth(k)
#        time.sleep(0.01)   
#    
#    now = time.time()
#    while time.time()-now<=3:
#        keep_yaw(to_180(yaw+angle), -50)
#        keep_depth(k)
#        time.sleep(0.01)
#    
#    now = time.time()
#    while time.time()-now<18:
#        keep_yaw(to_180(yaw+angle), -50)
#        keep_depth(k)
#        time.sleep(0.01)
#    
#    time.sleep(3)
#    
#    now = time.time()
#    while time.time()-now<20:
#        keep_yaw(to_180(yaw+angle), 50)
#        keep_depth(k)
#        time.sleep(0.01)
#    
#    while k>=0:
#        # Всплываем
#        keep_depth(k)
#        k-=0.01
#    
#    auv.set_motor_power(0, 0)
#    auv.set_motor_power(1, 0)
#    auv.set_motor_power(2, 0)
#    auv.set_motor_power(3, 0)
#    4 x 1 5
    
#    Повернули
#     while time.time()-now<=3:
#         keep_yaw(to_180(yaw+angle), 0)
#         keep_depth(k)
#         time.sleep(0.01)
#     print("повернул")
# #    Проплыли

#     now = time.time()
#     while time.time()-now<=3.5:
#         keep_yaw(to_180(yaw+angle), -50)
#         keep_depth(k)
#         time.sleep(0.01)
    
#     auv.set_motor_power(1, 0)
#     auv.set_motor_power(2, 0)
 
#     LED(6)
#     time.sleep(3)
#     touch()
    
#     now = time.time()
#     while time.time()-now<=3.5:
#         keep_yaw(to_180(yaw+angle), -50)
#         keep_depth(k)
#         time.sleep(0.01)
    
#     auv.set_motor_power(1, 0)
#     auv.set_motor_power(2, 0)
    
    
#     LED(4)
#     time.sleep(3)
    
#     now = time.time()
#     while time.time()-now<=5:
#         keep_yaw(to_180(yaw+angle), -50)
#         keep_depth(k)
#         time.sleep(0.01)
    
#     auv.set_motor_power(1, 0)
#     auv.set_motor_power(2, 0)
    
#     LED(1)    
#     time.sleep(3)
    
#     # КРУТИТСЯ ПО КРУГУ
#     rotate()
    
#     now = time.time()
#     while time.time()-now<=3.5:
#         keep_yaw(to_180(yaw+angle), -50)
#         keep_depth(k)
#         time.sleep(0.01)
    
#     LED(5)
#     time.sleep(3)
    
#     now = time.time()
#     while time.time()-now<=20:
#         keep_yaw(to_180(yaw+angle), 50)
#         keep_depth(k)
#         time.sleep(0.01)
    
#     print("вернулся")
#     while k>=0:
#         # Всплываем
#         keep_depth(k)
#         time.sleep(0.01)
#         k-=0.01
#     print("всплыл")
#     auv.set_motor_power(0, 0)
#     auv.set_motor_power(1, 0)
#     auv.set_motor_power(2, 0)
#     auv.set_motor_power(3, 0)
        
        
        
        
        
        
        
        
        

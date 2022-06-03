#import pymurapi as mur
import numpy as np
import math
import time
import cv2

# auv = mur.mur_init()
#
# p_time = 0
# p_error = 0.0
#
# prev_time = 0
# prev_error = 0.0
# def to_360(angle):
#     if angle > 0.0:
#         return angle
#     if angle <= 0.0:
#         return 360.0 + angle
#        
# def to_180(a):
#     if a > 180.0:
#         return a - 360
#     if a < -180.0:
#         return a + 360
#     return a
#    
# def clamp(v, max_v, min_v):
#     if v > max_v:
#         return max_v
#     if v < min_v:
#         return min_v
#     return v
#
# def keep_depth(value):
#     global p_time
#     global p_error
#    
#     c_time = int(round(time.time() * 1000))
#    
#     error_depth = auv.get_depth() - value
#    
#     power_2 = 0
#     power_3 = 0
#    
#     power_value = error_depth * 40
#     diff_value = 5 / (c_time - p_time) * (error_depth - p_error)
#    
#     power_2 = clamp(power_value + diff_value, 100, -100)
#     power_3 = clamp(power_value + diff_value, 100, -100)
#    
#     auv.set_motor_power(2, power_2)
#     auv.set_motor_power(3, power_3)
#    
#     p_time = c_time
#     p_error = error_depth
#
# def keep_yaw(value):
#     global prev_time
#     global prev_error
#    
#     current_time = int(round(time.time() * 1000))
#    
#     error_yaw = auv.get_yaw() - value
#     error_yaw = to_180(error_yaw)
#    
#     power_0 = 0
#     power_1 = 0
#    
#     power_value = error_yaw * 0.35
#     diff_value = 0.3 / (current_time - prev_time) * (error_yaw - prev_error)
#    
#     power_0 = clamp(power_value - diff_value, 100, -100)
#     power_1 = clamp(power_value + diff_value, 100, -100)
#    
#     auv.set_motor_power(0, -power_0)
#     auv.set_motor_power(1, power_1)
#    
#     prev_time = current_time
#     prev_error = error_yaw


# OpenCv2
color_black = (
    ( 0, 0,  0),
    ( 180, 255, 70)
)

color_orange = (
    ( 0, 140,  100),
    ( 12, 255, 255)
)

def search(shape, color, img):
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
        
        line_color = (0,0,255)
        
        # Нарисуем соответствующую описанную фигуру вокруг контура

        if shape_name == 'circle' and shape == 'circle':
#            cv2.circle(drawing, (int(circle_x), int(circle_y)), int(circle_radius), line_color, 2, cv2.LINE_AA)
            circles += 1

        if (shape_name == 'rect' or shape_name == 'square') and (shape == 'rect' or shape == 'square'):
#            cv2.drawContours(drawing, [box], 0, line_color, 2, cv2.LINE_AA)
            rect += 1
#        cv2.imshow('drawing', drawing)
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
    # auv = mur.mur_init()
    # mur_view = auv.get_videoserver()
    video = cv2.VideoCapture(0)
#    print(video)
    while True:
#        keep_depth(0.7)
#        time.sleep(0.03)
#        if auv.get_depth() < 0.75 and auv.get_depth() > 0.65:
#            auv.set_motor_power(0, 50)
#            auv.set_motor_power(1, 50)
        _, img = video.read()
#        img2 = img.copy()
#        contours = find_contours(img, color_orange)
#        for cnt in contours:
#            if cv2.contourArea(cnt) > 300:
#                  cv2.drawContours(img2, [cnt], 0, (255, 255, 255), 2, cv2.LINE_AA)
#        cv2.imshow("", img2)
        #cv2.imwrite('img.jpg', img)
        #img = cv2.imread('img.jpg')
        #print(img[470:472,638:640])
#        cv2.imwrite('img.jpg', img)
        print(search('circle', color_black, img))
#        img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # cv2.imshow('img', img)
        # mur_view.show(img, 0)
        # print(img)

        key_press = cv2.waitKey(30)
        #if key_press == ord('q'):
            #break
    #video.release()
    #cv2.destroyAllWindows()
#        cv2.imshow('img', img)
#        print(img)
#        print(search('rect', color_orange, img))
#        if search('rect', color_orange, img) != 0:
#            print("orange")
#            auv.set_motor_power(0, 0)
#            auv.set_motor_power(1, 0)
#            if (time.time() - now) > 15:
#                auv.set_motor_power(0, 0)
#                auv.set_motor_power(1, 0)
#                break
#    print(1234567)
#    while True:
#        keep_yaw(180)
##        auv.set_motor_power(0, 50)
##        auv.set_motor_power(1, 50)
##        keep_depth(0.7)
#        time.sleep(0.5)
#        if auv.get_depth() < 0.76 and auv.get_depth() > 0.65:
    
#        if (time.time() - now2) > 15:
#            auv.set_motor_power(0, 0)
#               auv.set_motor_power(1, 0)
        
        
#        keep_yaw(40)
#        time.sleep(0.03)

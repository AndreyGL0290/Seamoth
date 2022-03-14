import cv2
import numpy as np
def count_circles(image):
    obj = {}
    collisions = 0
    for y in range(len(image)):
        counter = 0
        for x in range(len(image[y]) - 1):
            # print(image[y,x])
            if image[y,x,2] == 0 and image[y,x+1,2] != 0:
                image[y,x,0] = 255
                image[y,x,1] = 0
                image[y,x,2] = 0
                counter += 2
        if counter % 2 == 1:
            obj[y] = counter-1
        else:
            obj[y] = counter
    # print(obj)
    for k, v in obj.items():
        if k != len(obj.keys())-1:
            if v >= obj[k+1]:
                continue
            else:
                n = obj[k+1]-v
                collisions += n//2
    cv2.imshow('1', image)

    return collisions

                
def find_circles(img):

    circles = 0
    # img = cv2.imread(img)

    # hsv
    # color = (
    #     ( 0,  0,  0),
    #     (40, 40, 40)
    # )

    # img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    drawing = img.copy()
    # cv2.drawContours(drawing, contours, -1, (255,255,255), 1)

    # circles = len(contours)


    # if contours:
    #     for i in range(len(contours)):
    #         cnt = contours[i]
            
    #         if cv2.contourArea(cnt) < 50:
    #             continue
    #         cv2.drawContours(drawing, contours, i, (0,0,255), 2)

    #         moments = cv2.moments(cnt)
    #         try:
    #             x = int(moments['m10'] / moments['m00'])
    #             y = int(moments['m01'] / moments['m00'])
    #             cv2.circle(drawing, (x,y), 4, (0,255,255), -1)
    #         except ZeroDivisionError:
    #             pass
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # подбираем параметры цветового фильтра для выделения
    # нашего объекта (указанные числовые значения могут
    # отличаться)
    hsv_min = np.array((0, 0, 0), np.uint8)
    hsv_max = np.array((255, 255, 50), np.uint8)
    # применяем цветовой фильтр к исходному изображению,
    # результат записываем в переменную hsv_msk
    hsv_msk = cv2.inRange( hsv_img, hsv_min, hsv_max ) 
    # ищем контуры и запqqисываем их в переменную contours
    # в режиме поиска всех контуров без группировки
    # cv2.RETR_LIST, для хранения контуров используем
    # метод cv2.CHAIN_APPROX_SIMPLE
    contours, _ = cv2.findContours( hsv_msk, 
    cv2.RETR_LIST,
    cv2.CHAIN_APPROX_SIMPLE)
    # перебираем все найденные контуры в цикле
    for icontour in contours:
    # выбираем контуры с длиной больше 40 точек
        if len(icontour)>40:
            circles += 1
            # записываем в переменную ellipse
            # отвечающий условию контур в форме эллипса
            ellipse = cv2.fitEllipse(icontour)
            # отображаем найденный эллипс
            cv2.ellipse(img, ellipse, (255,0,255), 2)
    # выводим итоговое изображение в окно contours
    cv2.imshow('contours', img) 
    # выводим результат фильтрации изображения в окно HSV
    # cv2.imshow('hsv', hsv_msk) 
    # ждем нажатия любой клавиши и закрываем все окна
    cv2.waitKey(25)

    # cv2.imshow("img", drawing)
    # cv2.waitKey(25)
            
    return circles
    # else:
        # circles_k_max = 1
        # for k,v in obj.items():
        #     if v > obj[circles_k_max]:
        #         circles_k_max = k

        # circles_k_min = 1
        # for k,v in obj.items():
        #     if v < obj[circles_k_min]:
        #         circles_k_min = k
        # return {'max': circles_k_max, 'min': circles_k_min}
        # return obj

# find_circles('ideal_1.jpg')

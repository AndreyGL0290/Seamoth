import cv2

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

                
def find_circles(number, obj={}):
    if number < 5:
        img = cv2.imread(f'ideal_{number}.jpg')

        # cv2.imshow('img', img)

        # hls
        color = (
            ( 74,  76,  76),
            (180, 255, 255),
        )

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_mask = cv2.inRange(img_rgb, color[0], color[1])
        # cv2.imshow('img', img_mask)

        # Выделим контуры из полученной маски.
        # Данная функция возвращает массив контуров, а также их иерархию.
        #
        # В аргументах этой функции помимо маски, также указывается
        # режим определения иерархии (установим такой режим, чтобы
        # оставался лишь внешний контур, а все вложенные будут отсекаться),
        # а также метод аппроксимации (упрощение контура, чтобы исключить
        # избыточные точки из каждого контура).

        contours, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Нарисуем выделенные контуры. Указываем изображение, на котором
        # будем рисовать, массив контуров, индекс контура (можно задать
        # значение индекса как -1, чтобы отобразить все контуры в массиве),
        # а также цвет и толщину обводки.

        drawing = img.copy()
        cv2.drawContours(drawing, contours, -1, (255,255,255), 1)

        circles = len(contours)

        obj[number] = circles

        if contours:
            # Можно было сделать цикл вида "for cnt in contours",
            # но здесь нам нужно иметь индекс текущего контура.
            for i in range(len(contours)):
                cnt = contours[i]

                # С помощью данного условия, мы можем отсеять
                # слишком маленькие контуры (т.е. такие контуры,
                # у которых слишком маленькая площадь).
                if cv2.contourArea(cnt) < 50:
                    continue
                cv2.drawContours(drawing, contours, i, (0,0,255), 2)

                # Определим геометричсекий центр конутра
                # с помощью т.н. "моментов изображения"
                moments = cv2.moments(cnt)
                try:
                    x = int(moments['m10'] / moments['m00'])
                    y = int(moments['m01'] / moments['m00'])
                    cv2.circle(drawing, (x,y), 4, (0,255,255), -1)
                # у нас может случится деление на ноль, и это надо предусмотреть.
                except ZeroDivisionError:
                    pass
                
                
                # cv2.imshow('drawing', drawing)
                cv2.imwrite(f'{number}_circles.jpg', drawing)
                # print(count_circles(drawing))
                cv2.waitKey(0)
        object = find_circles(number+1, obj)
        return object
    else:
        circles_k_max = 1
        for k,v in obj.items():
            if v > obj[circles_k_max]:
                circles_k_max = k

        circles_k_min = 1
        for k,v in obj.items():
            if v < obj[circles_k_min]:
                circles_k_min = k
        return {'max': circles_k_max, 'min': circles_k_min}


obj = find_circles(1)


print(obj)
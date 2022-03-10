import cv2
from math import sqrt

# # Эта функция закрашивает все круги
# def color_circle(image):
#     for y in range(len(image)):
#         for x in range(len(image[y])):
#             # print((image[y, x, 0] + image[y, x, 1] + image[y, x, 2]))
#             if int((int(image[y, x, 0]) + int(image[y, x, 1]) + int(image[y, x, 2])) / 3) < 200:
#                 image[y, x, 0] = 0
#                 image[y, x, 1] = 0
#                 image[y, x, 2] = 0
        
#     cv2.imshow("1", image)
#     cv2.waitKey(0)
#     cv2.imwrite('1_found.jpg', image)


# Нормальное округление
def int_r(num):
    num = int(num + (0.5 if num > 0 else -0.5))
    return num

def find_first_px(image):
    first_line = []
    for y in range(len(image)):
        for x in range(len(image[y])):
            if int((int(image[y, x, 0]) + int(image[y, x, 1]) + int(image[y, x, 2])) / 3) < 200:
                for x in range(len(image[y])):
                    if int((int(image[y, x, 0]) + int(image[y, x, 1]) + int(image[y, x, 2])) / 3) < 200:
                        first_line.append((x,y))
                # image[y, x, 0] = 0
                # image[y, x, 1] = 0
                # image[y, x, 2] = 255
                x, y = first_line[len(first_line)//2]
                return x, y

# Находит последний px круга
def find_last_px(image, x, y):
    for y_last in range(y, len(image)):
        if int((int(image[y_last, x, 0]) + int(image[y_last, x, 1]) + int(image[y_last, x, 2])) / 3) > 200:
            image[y_last-1, x, 0] = 0
            image[y_last-1, x, 1] = 0
            image[y_last-1, x, 2] = 255
            print(y_last-1)
            return y_last-1

def draw_circle(image, o, r):
    x = [r - n for n in range(1, 2 * int_r(r) + 1)]
    # print(x)
    obj = {}
    for i in range(len(x)):
        # print((r**2 - x[i]**2))
        obj[x[i] + o['x']] = [sqrt(r**2 - x[i]**2) + o['y'], -sqrt(r**2 - x[i]**2) + o['y']]
    
        image[int_r(obj[x[i] + o['x']][0]), int_r(x[i] + o['x']), 0] = 0
        image[int_r(obj[x[i] + o['x']][0]), int_r(x[i] + o['x']), 1] = 0
        image[int_r(obj[x[i] + o['x']][0]), int_r(x[i] + o['x']), 2] = 255
        image[int_r(obj[x[i] + o['x']][1]), int_r(x[i] + o['x']), 0] = 0
        image[int_r(obj[x[i] + o['x']][1]), int_r(x[i] + o['x']), 1] = 0
        image[int_r(obj[x[i] + o['x']][1]), int_r(x[i] + o['x']), 2] = 255




img = cv2.imread('1_resized.jpg', cv2.IMREAD_COLOR)
# print(image[100, 100])

x, y_first = find_first_px(img)

y_last = find_last_px(img, x, y_first)
r = (y_last - y_first) / 2
o = {"x": x, "y": y_first + r}

img[int_r(o['y']), int_r(o['x']), 0] = 0
img[int_r(o['y']), int_r(o['x']), 1] = 0
img[int_r(o['y']), int_r(o['x']), 2] = 255

# draw_circle(img, o, r)

cv2.imshow("1", img)
cv2.waitKey(0)
cv2.imwrite('1_found.jpg', img)

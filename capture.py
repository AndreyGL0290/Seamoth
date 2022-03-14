import cv2
import numpy as np

video = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:
    ret, frame = video.read()

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask1 = cv2.inRange(hsv, (50, 70, 0), (135, 255, 160))

    target = cv2.bitwise_and(frame, frame, mask=mask1)

    cv2.imshow('MASK', mask1)
    cv2.imshow('USUAL', frame)
    cv2.imshow('FINAL', target)
    cv2.imshow('HSV', hsv)
    print('Тень: ', hsv[360, 0], 'Круг: ', hsv[70, 480])
    key_press = cv2.waitKey(30)
    if key_press == ord('q'):
        cv2.imwrite('hsv.jpg', hsv)
        break

video.release()
cv2.destroyAllWindows()
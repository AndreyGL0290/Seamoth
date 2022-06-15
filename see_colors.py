from videoserver import VideoServer
import pymurapi as mur
import cv2

IS_AUV = True

auv = mur.mur_init()

mur_view = VideoServer()


if __name__ == '__main__':
    video1 = cv2.VideoCapture(0)
    video2 = cv2.VideoCapture(1)

    while True:
        _, frame1 = video1.read()
        _, frame2 = video2.read()


        mur_view.show(frame1, 0)
        mur_view.show(frame2, 1)

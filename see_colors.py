from videoserver import VideoServer
import pymurapi as mur
import cv2
import time

IS_AUV = True

auv = mur.mur_init()

mur_view = VideoServer()

def clamp(power, max, min):
    if power >= max:
        return max
    elif power < min:
        return min
    return power

prev_time = 0
prev_high_diff = 0

def keep_depth(depth):
    global prev_time, prev_high_diff
    current_time = int(round(time.time() * 1000))
    k = 300
    high_diff = auv.get_depth() - depth

    power_0 = 0
    power_3 = 0

    diff_value = 10 / (current_time - prev_time) * (high_diff - prev_high_diff)
    
    power_value = clamp(high_diff*k + diff_value, 40, -40)
    power_0 = power_value
    power_3 = power_value

#    print(power_0, power_3)
    
    auv.set_motor_power(0, power_0)
    auv.set_motor_power(3, power_3)

    prev_time = current_time
    prev_high_diff = high_diff

if __name__ == '__main__':
    video1 = cv2.VideoCapture(0)
    video2 = cv2.VideoCapture(1)
    
    now = time.time()
    while time.time() - now < 10:
        keep_depth(0.4)
        _, frame1 = video1.read()
        _, frame2 = video2.read()


        mur_view.show(frame1, 0)
        mur_view.show(frame2, 1)
        time.sleep(0.01)
    while True:
        auv.set_motor_power(0, 40)
        auv.set_motor_power(0, 40)

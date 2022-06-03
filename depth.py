import pymurapi as mur
from time import sleep, time

auv = mur.mur_init()

prev_time = 0
prev_high_diff = 0

def clamp(power):
    if power >= 100:
        return 100
    elif power < -100:
        return -100
    return power

def keep_depth(depth):
    global prev_time, prev_high_diff
    current_time = int(round(time() * 1000))
    k = 100
    high_diff = auv.get_depth() - depth

    power_0 = 0
    power_3 = 0

    diff_value = 10 / (current_time - prev_time) * (high_diff - prev_high_diff)
    if abs(high_diff) < 0.2:
        k = 200
    power_value = clamp(high_diff*k + diff_value)
    power_0 = power_value
    power_3 = power_value
    
    print(power_0, power_3)
    
    auv.set_motor_power(0, power_0)
    auv.set_motor_power(3, power_3)

    prev_time = current_time
    prev_high_diff = high_diff

if __name__ == '__main__':
    while True:
        keep_depth(0.5)
        sleep(0.01)
        

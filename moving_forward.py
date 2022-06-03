import pymurapi as mur
import time

auv = mur.mur_init()

def clamp(power, max, min):
    if power >= max:
        return max
    elif power < min:
        return min
    return power

def to_180(a):
    if a > 180.0:
        return a - 360
    if a < -180.0:
        return a + 360
    return a

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

def keep_yaw(yaw_to_set, speed = 0):
    try: 
        error = auv.get_yaw() - yaw_to_set 
        error = to_180(error)
        output = keep_yaw.regulator.process(error)
        output = clamp(output, 100, -100)
#        auv.set_motor_power(0, clamp((speed - output), 100, -100))#симулятор
#        auv.set_motor_power(1, clamp((speed + output), 100, -100))#симулятор
        if speed != 0:
            auv.set_motor_power(1, clamp(output + speed, 100, -100)) #Робот
            auv.set_motor_power(2, clamp(-output + speed, 100, -100)) #Робот
        else:
            auv.set_motor_power(1, output) #Робот
            auv.set_motor_power(2, -output) #Робот
        
        
    except AttributeError:
        keep_yaw.regulator = PD()
        keep_yaw.regulator.set_p_gain(1) # 0.8
        keep_yaw.regulator.set_d_gain(1) # 0.5

if __name__ == '__main__':
    # Пин 0, 3 - Правый, левый передние
    # Пин 1, 2 - Правый, левый задние
    time.sleep(1)
    yaw = auv.get_yaw()
    print(yaw)
    
    # Стабилизация
#    now = time.time()
#    while time.time() - now < 3:
#        # print('rotating')
#        keep_yaw(to_180(yaw))
#        time.sleep(0.01)

    # Поворот
    now = time.time()
    while time.time() - now < 4:
        # print('rotating')
        keep_yaw(to_180(yaw-90))
        time.sleep(0.01)

    # Движение вперед
#    counter = 0
#    while counter < 10:
#        # Удержание курса
    now = time.time()
    while time.time() - now < 5:
#        print('rotating')
        keep_yaw(to_180(yaw-90), -60)
        time.sleep(0.01)
    
    now = time.time()
    while time.time() - now < 4:
        # print('rotating')
        keep_yaw(to_180(yaw+90))
        time.sleep(0.01)
    
    now = time.time()    
    while time.time() - now < 5:
#        print('rotating')
        keep_yaw(to_180(yaw+90), -60)
        time.sleep(0.01)
    
        # Движение
#        now = time.time()
#        while time.time() - now < 0.5:
#             print('swimming')
#            auv.set_motor_power(1, -30)
#            auv.set_motor_power(2, -30)
#            time.sleep(0.01)
#        counter += 1
    
    # Поворот
#    now = time.time()
#    while time.time() - now < 4:
#        # print('rotating')
#        keep_yaw(to_180(yaw+90))
#        time.sleep(0.01)
#
#    # Движение назад
#    counter = 0
#    while counter < 10:
#        # Удержание курса
#        now = time.time()
#        while time.time() - now < 0.5:
#            # print('rotating')
#            keep_yaw(to_180(yaw+90))
#            time.sleep(0.01)
#        
#        # Движение
#        now = time.time()
#        while time.time() - now < 0.5:
#            # print('swimming')
#            auv.set_motor_power(1, -30)
#            auv.set_motor_power(2, -30)
#            time.sleep(0.01)
#        counter += 1
#
#    # Всплытие
#    now = time.time()
#    while time.time() - now < 7:
#        auv.set_motor_power(0, 40)
#        auv.set_motor_power(3, 40)

    # End of the program
    auv.set_motor_power(0, 0)
    auv.set_motor_power(1, 0)
    auv.set_motor_power(2, 0)
    auv.set_motor_power(3, 0)
    
    

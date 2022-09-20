def find_min_max(d: type [dict]):
    min_key = 999
    min_val = 999
    max_val = 0
    max_key = 0
    for k, v in d.items():
        if v > max_val:
            max_val = v
            max_key = k
        if v < min_val:
            min_val = v
            min_key = k
    return max_key, min_key

def rotate():
    print('rotated')

def touch():
    print('touched')

if __name__ == '__main__':
    circles = {1:4, 2:2, 3:5, 4:6, 5:1}

    position = list(circles.keys())[-1]

    key_max, key_min = find_min_max(circles)
    # print(key_min, key_max)
    to_do = {key_min: rotate, key_max: touch}

    first = key_min
    if key_min < key_max:
        first = key_max
    
    counter = 0
    while counter < position - first: # Едем к ближайшей табличке с крайним значением
        # Едим вперед
        counter += 1
    
    # print(position - counter)
    to_do[first]()

    position = first
    second = key_max
    if second > key_min:
        second = key_min
    
    counter = 0
    while counter < position - second: # Едем к следующей табличке с крайним значением
        # Едим вперед
        counter += 1
    
    # print(position - counter)
    to_do[second]()


    position = second
    counter = 1
    while counter < position: # Едем в начало
        # Едим вперед
        counter += 1
    
    # print((counter - position) == 0)

    # Код для всплытия
    # auv.set_motor_power(1, 0)
    # auv.set_motor_power(2, 0)
    # auv.set_motor_power(3, 0)
    # auv.set_motor_power(4, 0)
    
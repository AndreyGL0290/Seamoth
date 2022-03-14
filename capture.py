import cv2
import mss
import numpy
from contures import find_circles

with mss.mss() as sct:
    # Part of the screen to capture
    monitor = {"top": 40, "left": -960, "width": 960, "height": 480}

    while "Screen capturing":
        # Get raw pixels from the screen, save it to a Numpy array
        img = numpy.array(sct.grab(monitor))

        # Display the picture
        # cv2.imshow("OpenCV/Numpy normal", img)

        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        print(find_circles(img))
        
        # Press "q" to quit
        if cv2.waitKey(25) & 0xFF == ord("q"):
            cv2.destroyAllWindows()
            break
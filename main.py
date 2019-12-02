import math
import sys
import cv2
import numpy as np
from statistics import mean
from glob import glob

files = glob('myphotos/*.jpg')
number_of_pictures = len(files)


class Dot:
    def __init__(self, contour):
        self.contour = contour
        x_coords = []
        y_coords = []
        for con_point in contour:
            con_x = con_point[0][1]
            con_y = con_point[0][0]
            x_coords.append(con_x)
            y_coords.append(con_y)
        self.x = mean(x_coords)
        self.y = mean(y_coords)
        self.has_dice = False
        self.radius = cv2.arcLength(contour, True) / 6.28

    def distance_to(self, other_dot):
        return math.sqrt(((self.x - other_dot.x) ** 2) + ((self.y - other_dot.y) ** 2))


class Dice:
    def __init__(self):
        self.dots = []
        self.result = 0

    def add_dot(self, dot):
        self.dots.append(dot)
        self.result += 1
        dot.has_dice = True

    def try_add_dot(self, dot):
        for my_dot in self.dots:
            if my_dot.distance_to(dot) < 7 * dot.radius:
                self.add_dot(dot)
                return True
        return False

    def draw_rectangle(self, image):
        max_x = 0
        min_x = image.shape[0]
        max_y = 0
        min_y = image.shape[1]
        for dot in self.dots:
            for con_point in dot.contour:
                con_x = con_point[0][1]
                con_y = con_point[0][0]
                if con_x > max_x:
                    max_x = con_x
                if con_x < min_x:
                    min_x = con_x
                if con_y > max_y:
                    max_y = con_y
                if con_y < min_y:
                    min_y = con_y
        wsp_skal = 1.5
        if self.result == 1:
            wsp_skal = 5
        sr_x = (min_x + max_x) / 2
        sr_y = (min_y + max_y) / 2
        delta = wsp_skal * max(max_x - min_x, max_y - min_y) / 2
        x1 = int(sr_x + delta)
        x0 = int(sr_x - delta)
        y1 = int(sr_y + delta)
        y0 = int(sr_y - delta)
        cv2.rectangle(image, (y0, x0), (y1, x1), (0, 255, 0), 3)
        cv2.putText(image, str(self.result), (int(sr_y) - 7, x0 - 6), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2,
                    cv2.LINE_AA)


def create_window(window_name):
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 900, 600)
    cv2.moveWindow(window_name, 0, 0)


def find_contours(gray_image):
    image = cv2.GaussianBlur(gray_image, (15, 15), 3)
    image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 1)
    kernel = np.ones((5, 5), np.uint8)
    image = cv2.erode(image, kernel, iterations=1)
    image = cv2.dilate(image, kernel, iterations=1)
    contours, _ = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def draw_dots(contours, image):
    dots = []
    cont_nr = []
    for j in range(len(contours)):
        area = cv2.contourArea(contours[j])
        perimeter = cv2.arcLength(contours[j], True)
        if perimeter == 0:
            break
        circularity = 4 * math.pi * (area / (perimeter * perimeter))
        if 0.8 < circularity and 100 < area < 2500:
            dot = Dot(contours[j])
            dots.append(dot)
            cont_nr.append(j)

    big_dots = []
    max_radius = 0
    for dot in dots:
        if dot.radius > max_radius:
            max_radius = dot.radius
    for i in range(len(dots)):
        dot = dots[i]
        if dot.radius > 0.75 * max_radius:
            big_dots.append(dot)
            cv2.drawContours(image, contours, cont_nr[i], (0, 0, 255), 3)

    return big_dots


def create_dices(dots):
    dices = []
    for dot in dots:
        if dot.has_dice:
            continue
        for dice in dices:
            if dice.try_add_dot(dot):
                break
        if not dot.has_dice:
            dice = Dice()
            dice.add_dot(dot)
            dices.append(dice)
    return dices


def main_photos():
    for i in range(number_of_pictures):
        window_name = 'Dice' + str(i + 1)
        create_window(window_name)

        original_image = cv2.imread(files[i], cv2.IMREAD_COLOR)
        if original_image.shape[0] > original_image.shape[1]:
            original_image = cv2.rotate(original_image, cv2.ROTATE_90_CLOCKWISE)

        processed_image = original_image.copy()
        gray_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)

        contours = find_contours(gray_image)

        dots = draw_dots(contours, processed_image)

        dices = create_dices(dots)

        result = 0

        for dice in dices:
            dice.draw_rectangle(processed_image)
            result += dice.result

        cv2.putText(processed_image, "Suma: " + str(result), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3,
                    cv2.LINE_AA)

        cv2.imshow(window_name, original_image)
        cv2.imwrite('results/' + str("{:02d}".format(i + 1)) + '.jpg', processed_image)

        key = cv2.waitKey(0)

        if key == 13:  # enter
            cv2.imshow(window_name, processed_image)
            key = cv2.waitKey(0)
        if key == 27:  # esc
            sys.exit()
        cv2.destroyAllWindows()


def run_algorithm(image):

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    contours = find_contours(gray_image)

    dots = draw_dots(contours, image)

    dices = create_dices(dots)

    result = 0

    for dice in dices:
        dice.draw_rectangle(image)
        result += dice.result

    cv2.putText(image, "Suma: " + str(result), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3,
                cv2.LINE_AA)
    return image


def main_camera():
    cap = cv2.VideoCapture(2)
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1600)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 900)

    while True:
        try:
            ret, image = cap.read()
            done_image = run_algorithm(image)
            cv2.imshow('object detection', done_image)
            # exit when escape
            if cv2.waitKey(1) == 27:
                cap.release()
                cv2.destroyAllWindows()
                break
        except:
            cap.release()


if __name__ == '__main__':
    main_camera()

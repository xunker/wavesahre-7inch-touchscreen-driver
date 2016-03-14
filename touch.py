#!/usr/bin/env python3

import struct
import time
import math
import glob
import uinput
import pyudev
import os


def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

# Wait and find devices
def read_and_emulate_mouse(deviceFound):
    with open(deviceFound, 'rb') as f:
        print("Read buffer")

        device = uinput.Device([
            uinput.BTN_LEFT,
            uinput.BTN_RIGHT,
            uinput.ABS_X,
            uinput.ABS_Y,
        ])

        clicked = False
        rightClicked = False
        (lastX, lastY) = (0, 0)
        startTime = time.time()
        calibration = 22
        width = 800
        height = 480

        screen_x_min = 110
        screen_x_max = 3980
        screen_y_min = 280
        screen_y_max = 3860

        while True:
            b = f.read(22)
            (tag, btnLeft, x, y) = struct.unpack_from('>c?HH', b)
            # print("A=======",tag, btnLeft, x, y)
            x = int(translate(x, screen_x_min, screen_x_max, 0, width))
            y = int(translate(y, screen_y_min, screen_y_max, 0, height))
            # print("B=======",tag, btnLeft, x, y)
            time.sleep(0.01) 

            if btnLeft:
                if x > 0:
                    # print("X:", x)
                    device.emit(uinput.ABS_X, x, True)
                if y > 0:
                    # print("Y:", y)
                    device.emit(uinput.ABS_Y, y, True)

                if not clicked:
                    # print("Left click")
                    device.emit(uinput.BTN_LEFT, 1)
                    clicked = True
                    startTime = time.time()
                    (lastX, lastY) = (x, y)

                duration = time.time() - startTime
                movement = math.sqrt(pow(x - lastX, 2) + pow(y - lastY, 2))

                if clicked and (not rightClicked) and (duration > 1) and (movement < 20):
                    # print("Right click")
                    device.emit(uinput.BTN_RIGHT, 1)
                    device.emit(uinput.BTN_RIGHT, 0)
                    rightClicked = True
            else:
                # print("Release")
                clicked = False
                rightClicked = False
                device.emit(uinput.BTN_LEFT, 0)

if __name__ == "__main__":
    os.system("modprobe uinput")
    os.system("chmod 666 /dev/hidraw*")
    os.system("chmod 666 /dev/uinput*")

    while True:
        # try:
        print("Waiting device")
        hidrawDevices = glob.glob("/dev/hidraw*")

        context = pyudev.Context()

        deviceFound = None
        for hid in hidrawDevices:
            device = pyudev.Device.from_device_file(context, hid)
            if "0EEF:0005" in device.device_path:
                deviceFound = hid

        if deviceFound:
            print("Device found", deviceFound)
            read_and_emulate_mouse(deviceFound)
            # except:
            #     print("Error:", sys.exc_info())
            #     pass
            # finally:
            #     time.sleep(1)

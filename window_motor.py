import sys
import time
import RPi.GPIO as GPIO


delay = 0.0050
steps = 500

# Enable pins for IN1-4 to control step sequence
coil_A_1_pin = 23
coil_A_2_pin = 24
coil_B_1_pin = 4
coil_B_2_pin = 17


def setup():
    """ Setup GPIO board """
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Set pin states
        GPIO.setup(coil_A_1_pin, GPIO.OUT)
        GPIO.setup(coil_A_2_pin, GPIO.OUT)
        GPIO.setup(coil_B_1_pin, GPIO.OUT)
        GPIO.setup(coil_B_2_pin, GPIO.OUT)

    except KeyboardInterrupt:
        GPIO.cleanup()


def set_step(w1, w2, w3, w4):
    """ Step sequence """
    GPIO.output(coil_A_1_pin, w1)
    GPIO.output(coil_A_2_pin, w2)
    GPIO.output(coil_B_1_pin, w3)
    GPIO.output(coil_B_2_pin, w4)


def open_window():
    """ Setup pins and open the window """
    setup()

    for i in range(0, steps):
        set_step(1,0,1,0)
        time.sleep(delay)
        set_step(0,1,1,0)
        time.sleep(delay)
        set_step(0,1,0,1)
        time.sleep(delay)
        set_step(1,0,0,1)
        time.sleep(delay)

    GPIO.cleanup()


def close_window():
    """ Setup pins and close the window """
    setup()

    for i in range(0, steps):
        set_step(1,0,0,1)
        time.sleep(delay)
        set_step(0,1,0,1)
        time.sleep(delay)
        set_step(0,1,1,0)
        time.sleep(delay)
        set_step(1,0,1,0)
        time.sleep(delay)

    GPIO.cleanup()


# Find out if we are closing or opening the window and call the right method
arg = sys.argv[1]

if arg == 'open':
    open_window()
elif arg == 'close':
    close_window()
else:
    sys.exit()

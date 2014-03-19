import threading
from random import randint
import os
import json


class Weather:
    def __init__(self):
        self.temp = 15
        self.pressure = 1000
        self.humidity = 30
        self.wind = dict(speed=10, angle=210)

    def simulate_weather(self):
        self.temp = min(max(self.temp + randint(-5, 5), -30), 30)
        self.humidity = min(max(self.humidity + randint(-5, 5), 70), 90)
        self.wind['angle'] = (self.wind['angle'] + randint(-5, 5)) % 360
        self.wind['speed'] = min(max(self.wind['speed'] + randint(-5, 5), 0), 40)


w = Weather()

def send_data():
    w.simulate_weather()
    os.system('curl -X POST -H "Content-Type: application/json" -d \'{}\' http://localhost:5000/api/weather_sensor_data'.format(json.dumps(w.__dict__)))
    threading.Timer(1, send_data).start()

send_data()

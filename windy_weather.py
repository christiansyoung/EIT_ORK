import os
from config import SERVICE_URL
import threading


def send_data():
    os.system('curl -X POST -H "Content-Type: application/json" -d \''
              '{"pressure": 1000, "wind": {"angle": 300, "speed": 29}, "temp": 15, "humidity": 79}\' '
              'http://%s/api/weather_sensor_data' % SERVICE_URL)
    threading.Timer(5, send_data).start()

send_data()

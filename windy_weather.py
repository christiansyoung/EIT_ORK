import os
from config import SERVICE_URL

os.system('curl -X POST -H "Content-Type: application/json" -d \''
          '{"pressure": 1000, "wind": {"angle": 300, "speed": 29}, "temp": 15, "humidity": 79}\' '
          'http://%s/api/weather_sensor_data' % SERVICE_URL)
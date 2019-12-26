kill -15 $(ps aux | grep sensor_data.py | awk '{print $2}')

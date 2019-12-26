import subprocess
import requests
import time


def automate():
    resp = requests.get('http://0.0.0.0:5000')
    with open('index.html', 'w') as f:
        f.write(resp.text)
    subprocess.call(["git", "add", "index.html"])
    subprocess.call(["git", "add", "sensor_data.csv"])
    subprocess.call(["git", "commit", "-m update"])
    subprocess.call(["git", "push"])


if __name__ == '__main__':
    time.sleep(5)  # wait for flask server to start
    while True:
        automate()
        time.sleep(60*5)


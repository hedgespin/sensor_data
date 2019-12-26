import requests
from bs4 import BeautifulSoup
import time
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.dates import HourLocator, DateFormatter

pd.options.display.float_format = '{:.2f}'.format


def cleanup(x):
    return x.replace('%', '') \
        .replace('Temperature in', '') \
        .replace(':', '') \
        .replace('*C', '') \
        .replace('*F', '') \
        .replace('\n', '') \
        .replace('\r', '').strip().split('  ')


def get_data():
    try:
        resp = requests.get("http://10.0.0.78")
        # print(resp.text)
        soup = BeautifulSoup(resp.text, 'html.parser')
        return [cleanup(x.text) for x in soup.find_all("h3") if len(cleanup(x.text)) > 1]
    except Exception as ex:
        print(ex)
        return None


def store_data(data):
    if data:
        with open('sensor_data.csv', 'a') as f:
            # f.write('Time,' + ','.join([x[0] for x in data]) + '\n')
            # print('Time,' + ','.join([x[0] for x in data]))
            f.write(str(time.ctime()) + ',' + ','.join([x[1] for x in data]) + '\n')
            print(str(time.ctime()) + ',' + ','.join([x[1] for x in data]))


def load_data_frame():
    df = pd.read_csv('sensor_data.csv', parse_dates=['Time'])
    df = df.set_index('Time')
    df = df.rolling('30T').min().interpolate()
    # df = df.resample('10T').median()
    # df = df.resample('H', label='right').mean().resample('T').mean().interpolate(method='cubic')
    return df


def plot(show=True):
    df = load_data_frame().last('48H')  # .tail(24)
    plt.figure(figsize=(10, 6))
    ax = plt.subplot()
    ax.plot(df['Humidity'])
    # ax.plot(df['Fahrenheit'])
    ax.legend(['Humidity', 'Temperature *F'])
    ax.format_xdata = DateFormatter('%d %b %I:%M %p')
    # ax.xaxis.set_major_locator(HourLocator(interval=1))
    ax.xaxis.set_major_formatter(DateFormatter('%I:%M %p\n%d %b'))
    ax.grid(linestyle='-.')
    plt.savefig("static/img_sensor_data.svg")

    if show:
        plt.show()
    else:
        plt.close()

    return df['Humidity'][-1:].item(), df['Humidity'].min()


class AlertManager:

    def __init__(self, threshold):
        self.minimum_threshold = threshold
        self.threshold = threshold
        pass

    @staticmethod
    def load_data_frame():
        df = pd.read_csv('sensor_data.csv', parse_dates=['Time'])
        df = df.set_index('Time')
        df = df.rolling('30T').min().interpolate()
        # df = df.resample('10T').median()
        # df = df.resample('H', label='right').mean().resample('T').mean().interpolate(method='cubic')
        return df

    def alert_humidity_rising(self):
        df = self.load_data_frame().last('48H')

        current_humidity = float('{:.2f}'.format(df['Humidity'][-1:].item()))
        previous_humidity = float('{:.2f}'.format(df['Humidity'][-2:-1].item()))
        min_humidity = float('{:.2f}'.format(df['Humidity'].min()))
        max_humidity = float('{:.2f}'.format(df['Humidity'].max()))

        return self.alert(min_humidity, max_humidity, current_humidity, previous_humidity)

    def alert(self, min_humidity, max_humidity, current_humidity, previous_humidity):
        if current_humidity > previous_humidity and current_humidity - min_humidity >= self.threshold:
            requests.post(
                'https://maker.ifttt.com/trigger/humidity_rising/with/key/xXGvEiLeXtd3rY4MTkxlp5yVzCMtYP3J2YEL5NhZ9r'
                , data={"value1": self.threshold, "value2": min_humidity, "value3": current_humidity})
            print("Humidity Rising more than {}%, {}% -> {}%"
                  .format(self.threshold, min_humidity, current_humidity))
            self.threshold += 1  # increase threshold for next alert
            return True

        if current_humidity < previous_humidity \
                and self.threshold > self.minimum_threshold \
                and max_humidity - current_humidity >= self.minimum_threshold:
            print("Humidity going down now")
            self.threshold = self.minimum_threshold

        return False


if __name__ == "__main__":
    alert_m = AlertManager(threshold=3)
    while True:
        try:
            store_data(get_data())
            plot(show=False)
            alert_m.alert_humidity_rising()

            import git_sensor_data
            git_sensor_data.automate()
        except Exception as ex:
            print(ex)

        print("Iteration done, sleeping for 5 minutes ...")
        time.sleep(60*5)

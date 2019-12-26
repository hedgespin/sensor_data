from flask import Flask, render_template, Markup

app = Flask(__name__)


@app.route("/")
def sensor_data():
    with open('sensor_data.csv', 'r') as f:
        lines = f.readlines()
        headers = [x.strip() for x in lines[0].split(',')]
        data = [x.strip() for x in lines[-1].split(',')]
    print(headers, data)
    return render_template('index_sensor_data.html', headers=headers, columns=data,
                           svg=Markup(open('static/img_sensor_data.svg').read()))


@app.after_request
def add_header(response):
    response.headers[
        'Cache-Control'] = 'no-store, no-cache, must-revalidate, post - check = 0, pre - check = 0, max - age = 0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0')

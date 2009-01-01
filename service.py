import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify
from utils import ReverseProxied

# ID on the active window from the database
ACTIVE_WINDOW = 1

app = Flask('webservice')

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'database.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    #USERNAME='admin',
    #PASSWORD='default'
))

app.config.from_envvar('FLASK_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def query_db(query, args=(), one=False):
    """Easy queries to the database."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def get_latest_sensor_data():
    row = query_db("select * from sensordata order by id desc limit 1;", one=True)

    return {
        u'pressure': row['preasure'],
        u'temp': row['temperature'],
        u'wind':
            {
                u'speed': row['wind_speed'],
                u'angle': row['wind_angle']
            },
        u'humidity': row['humidity']
    }

@app.route('/')
def index():
    db = get_db()
    #db.execute('INSERT INTO sensordata (wind_angle, wind_power, rain) VALUES (?,?,?)',
    #    [22,33,True])
    #db.commit()
    flash('Yo, this is the shit.')

    return render_template('status.html', **get_latest_sensor_data())

@app.route('/api/weather_sensor_data', methods=['POST'])
def post_sensor_data():
    weather = request.get_json()

    db = get_db()
    db.execute('INSERT INTO sensordata (window_id, wind_angle, wind_speed, temperature, preasure, humidity) '
               'VALUES (?,?,?,?,?,?)', [ACTIVE_WINDOW, weather['wind']['angle'], weather['wind']['speed'], weather['temp'], weather['pressure'], weather['humidity']])
    db.commit()

    return jsonify({'ok': True})

@app.route('/api/weather_data', methods=['get'])
def weather_data():
    return jsonify(get_latest_sensor_data())

@app.route('/configuration', methods=['GET', 'POST'])
def configuration():
    if request.method == 'POST':
        db = get_db()
	window_width = request.form['windowWidth']
	window_height = request.form['windowHeight']
	room_area = request.form['roomArea']
	window_direction = request.form['windowDirection']
	room_draft = request.form['roomDraft']
	window_hinge = request.form['windowHinge']
	db.execute('UPDATE configuration SET width=?, height=?, angle=?, draftthreshold=? WHERE window_id=?',[window_width, window_height, window_direction, room_draft, 1])
	db.commit()
	flash('Updated')
    return render_template('configuration.html')


app.wsgi_app = ReverseProxied(app.wsgi_app)

if __name__ == '__main__':
    app.run(debug=True)

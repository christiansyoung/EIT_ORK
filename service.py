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
    
    # If this is a timer call
    if request.method == 'POST':

        # POST parameters to variables
        hours = request.POST.get('hours')
        minutes = request.POST.get('minutes')

        # Make a new timer object
        db.execute('INSERT INTO timer (window_id, hour, minute) VALUES (?,?,?)', [ACTIVE_WINDOW, hours, minutes])
        db.commit()

        # Get the object we just created
        timer = query_db('SELECT id FROM timer order by id DESC', one=True)

        # If that does not exist, something is wrong
        if timer is None:
            flash('Something went wrong')
            return render_template('status.html', alert='danger')

        # Set the timer in the state
        timer_id = timer['id']    
        db.execute('UPDATE state SET timer_id=? WHERE window_id=?', [timer_id, ACTIVE_WINDOW])
        db.commit()

        flash('The timer was set!')
        return render_template('status.html', alert='success')

    state = query_db('SELECT * from state WHERE window_id=?', [ACTIVE_WINDOW], one=True)


    return render_template('status.html', state=state, **get_latest_sensor_data())


@app.route('/api/mode/')
def mode(mode):
    db = get_db()

    # Find the mode we are switching to and produces messages there after    
    auto = True
    flash_text = 'You are now in auto mode'
    alert = 'success'

    if mode == 'manual':
        auto = False
        flash_text = 'Warning! You are now in manual mode.'
        alert = 'warning'

    # TODO CHECK THRESH HERE. If it is dangerous, we must inform the user.

    db.execute('UPDATE state SET auto=? WHERE window_id=?', [auto, ACTIVE_WINDOW])
    db.commit

    flash(flash_text)

    return render_template('status.html', alert=alert)


@app.route('/api/open-close')
def open_close():
    window_open = False
    flash_text = 'Your window is now closed.'

    # Get the state and check whether the window is open or closed
    state = query_db('SELECT * from state WHERE window_id=?', [ACTIVE_WINDOW], one=True)
    if state is None:
        flash('Serious error')
        return render_template('status.html', alert='danger')

    # If it is now closed, open it.
    if state['open'] == False:
        window_open = True
        flash_text = 'Your window is now open.'

    db = get_db()
    db.execute('UPDATE state SET open=? WHERE window_id=?', [window_open, ACTIVE_WINDOW])
    db.commit()

    # OPEN WINDOW WITH MOTOR HERE

    flash(flash_text)
    return render_template('status.html', alert='success')


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
	db.execute('UPDATE configuration SET width=?, height=?, area=?, hinge=?, angle=?, draftthreshold=? WHERE window_id=?',[window_width, window_height, room_area, window_hinge, window_direction, room_draft, ACTIVE_WINDOW])
	db.commit()
	flash('Updated')
    return render_template('configuration.html')


app.wsgi_app = ReverseProxied(app.wsgi_app)

if __name__ == '__main__':
    app.run(debug=True)

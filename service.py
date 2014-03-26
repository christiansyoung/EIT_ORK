import os
import sqlite3
import datetime

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify
from flask.ext.login import LoginManager, login_required, login_user, logout_user

from forms import LoginForm, ConfigForm
from utils import ReverseProxied
from models import User
from config import SERVICE_URL

import formulas

# ID on the active window from the database
ACTIVE_WINDOW = 1

app = Flask('webservice')
app.config.from_object('config')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'database.db'),
    CSRF_ENABLED = True
))

WTF_CSRF_SECRET_KEY = app.config['SECRET_KEY']
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
    row = query_db("select * from sensordata order by timestamp desc limit 1;", one=True)

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


@login_manager.user_loader
def load_user(userid):
    return User.get(userid)


@app.route('/', methods=['GET'])
@login_required
def index():
    state = query_db('select * from state s LEFT JOIN timer on timer_id = id WHERE s.window_id=?', [ACTIVE_WINDOW], one=True)

    # If this is a timer call
    time = None
    if state['timestamp']:
        # converting timestamp to HH:MM
        time = state['timestamp'].split()[1].split(".")[0]
    return render_template('status.html', SERVICE_URL=SERVICE_URL, state=state, time=time, **get_latest_sensor_data())


@app.route('/api/set-timer/', methods=['POST'])
@login_required
def set_timer():
    state = query_db('SELECT * from state WHERE window_id=?', [ACTIVE_WINDOW], one=True)

    db = get_db()
    # POST parameters to variables
    hours = request.form['hours']
    minutes = request.form['minutes']
    timestamp = datetime.datetime.today()+datetime.timedelta(hours=int(hours), minutes=int(minutes))

    # Make a new timer object
    db.execute('INSERT INTO timer (window_id, timestamp) VALUES (?,?)', [ACTIVE_WINDOW, timestamp])
    db.commit()

    # Get the object we just created
    timer = query_db('SELECT id FROM timer order by id DESC', one=True)

    # If that does not exist, something is wrong
    if timer is None:
        flash('Something went wrong', 'danger')
        return render_template('status.html', state=state, **get_latest_sensor_data())

    # Set the timer in the state
    timer_id = timer['id']
    db.execute('UPDATE state SET timer_id=? WHERE window_id=?', [timer_id, ACTIVE_WINDOW])
    db.commit()

    try:
        if not state['open']:
            open_window()
        flash('The timer was set.', 'success')
    except Exception as e:
        flash(e.message, "danger")

    return redirect(url_for('index'))


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            if not request.form['password'] == app.config['PASSWORD'] or not request.form['name'] == app.config['USERNAME']:
                flash('Wrong username or password', 'danger')
            else:
                user = User()
                login_user(user)
                flash('You are now logged in!', 'success')
                return redirect(request.args.get("next") or url_for("index"))
        else:
            flash('CSRF validation failed.', 'danger')
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You are now logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/api/mode/<mode>')
@login_required
def mode(mode):
    db = get_db()

    # Find the mode we are switching to and produces messages there after    
    auto = True
    flash_text = 'You are now in auto mode.'
    alert = 'success'

    if mode == 'manual':
        auto = False
        flash_text = 'Warning! You are now in manual mode.'
        alert = 'danger'

    # TODO CHECK THRESH HERE. If it is dangerous, we must inform the user.

    db.execute('UPDATE state SET auto=? WHERE window_id=?', [auto, ACTIVE_WINDOW])
    db.commit()

    flash(flash_text, alert)

    return redirect(url_for('index'))


def open_window():
    code = os.system('python window_motor.py open')
    if code != 0:
        raise Exception('Your window could not be opened. (%s)' % code)
    db = get_db()
    db.execute('UPDATE state SET open=? WHERE window_id=?', [True, ACTIVE_WINDOW])
    db.commit()


def close_window():
    code = os.system('python window_motor.py close')
    if code != 0:
        raise Exception('Your window could not be closed. (%s)' % code)
    db = get_db()
    db.execute('UPDATE state SET open=? WHERE window_id=?', [False, ACTIVE_WINDOW])
    db.commit()


@app.route('/api/open-close/')
@login_required
def open_close():
    # Get the state and check whether the window is open or closed
    state = query_db('SELECT * from state WHERE window_id=?', [ACTIVE_WINDOW], one=True)
    if state is None:
        flash('Serious error', 'danger')
        return render_template('status.html', alert='danger')

    try:
        if not state['open']:
            weather = get_latest_sensor_data()
            # Dry run the close if needed method to check if it is dangerous to open based on latest sensor data
            if close_window_if_needed(weather, True):
                flash('Cannot open your window. It will break if I do. (Override this in manual)', 'danger')
                return redirect(url_for('index'))

            open_window()
            flash_text = 'Your window is now open.'
        else:
            close_window()
            flash_text = 'Your window is now closed.'
        flash(flash_text, 'success')
    except Exception as e:
        flash(e.message, "danger")
    return redirect(url_for('index'))

def close_window_if_needed(weather, dry_run=False):
    state = query_db('select * from state s LEFT JOIN timer on timer_id = id WHERE s.window_id=?', [ACTIVE_WINDOW], one=True)

    if not state['open']:
        return

    config = query_db("select * from configuration where window_id=?", [ACTIVE_WINDOW], one=True)
    args = dict(
        wind_speed=weather['wind']['speed'],
        width=config['width'],
        height=config['height'],
        wind_direction=weather['wind']['angle'],
        window_angle=config['angle'],
        window_opening_angle=45,
        motor_torsion=config['enginepower'],
        left_hinge=config['hinge'] == 1
    )

    if formulas.must_close_window(**args) or formulas.room_wind_speed(**args) > config['draftthreshold']:
        # If this is a dry run, don't actually close, but return true
        if dry_run:
            return True
        else:    
            close_window()

    # Return false if the formulas didn't trigger on dry run
    if dry_run:
        return False

    # Close window if the timer has expired
    if state['timestamp']:
        if datetime.datetime.strptime(state['timestamp'], "%Y-%m-%d %H:%M:%S.%f") < datetime.datetime.now():
            close_window()
            db = get_db()
            db.execute("UPDATE state SET timer_id=NULL where window_id=?;",[ACTIVE_WINDOW])
            db.commit()


MAX_SENSORDATA_ROWS = 100
@app.route('/api/weather_sensor_data', methods=['POST'])
def post_sensor_data():
    weather = request.get_json()

    close_window_if_needed(weather)

    db = get_db()
    count = query_db("select count(*) from sensordata", one=True)['count(*)']
    # delete rows in sensordata table if row count exceeds MAX_SENSORDATA_ROWS
    if count >= MAX_SENSORDATA_ROWS:
        db.execute("DELETE FROM sensordata WHERE timestamp IN "
                   "(SELECT timestamp FROM sensordata ORDER BY timestamp LIMIT ?);", [count-MAX_SENSORDATA_ROWS+1])
    db.execute('INSERT INTO sensordata (window_id, wind_angle, wind_speed, temperature, preasure, humidity) '
               'VALUES (?,?,?,?,?,?)',[
                   ACTIVE_WINDOW, 
                   weather['wind']['angle'], 
                   weather['wind']['speed'], 
                   weather['temp'], 
                   weather['pressure'], 
                   weather['humidity']])
    db.commit()

    return jsonify({'ok': True})


@app.route('/api/weather_data', methods=['get'])
def weather_data():
    return jsonify(get_latest_sensor_data())


@app.route('/configuration', methods=['GET', 'POST'])
@login_required
def configuration():
    form = ConfigForm()
    db = get_db()

    if request.method == 'POST':
        if form.validate_on_submit():
            db.execute('UPDATE configuration SET width=?, height=?, area=?, hinge=?, angle=?, draftthreshold=? WHERE window_id=?',[
                form.window_width.data, 
                form.window_height.data, 
                form.area.data, 
                form.window_hinge.data, 
                form.window_direction.data, 
                form.draft.data, 
                ACTIVE_WINDOW])
            db.commit()
            flash('Configuration updated', 'success')
        else:
            flash('Invalid input', 'danger')

    config = query_db('SELECT * FROM configuration WHERE window_id=?', [ACTIVE_WINDOW], one=True)
    if config is None:
        flash('No configuration set', 'danger')
        return render_template('configuration.html', form=form)

    form = ConfigForm(
        window_width=config['width'], 
        window_height=config['height'], 
        area=config['area'], 
        window_direction=config['angle'], 
        draft=config['draftthreshold'], 
        window_hinge=config['hinge'])
    return render_template('configuration.html', form = form)


app.wsgi_app = ReverseProxied(app.wsgi_app)

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])

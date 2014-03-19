import os
import sqlite3
import datetime

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify
from flask.ext.login import LoginManager, login_required, login_user, logout_user

from forms import LoginForm
from utils import ReverseProxied
from config_form import ConfigForm
from models import User

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
    CSRF_ENABLED = True,
    DEBUG=True,
    #USERNAME='admin',
    #PASSWORD='default'
    SECRET_KEY='development key',
    USERNAME='root',
    PASSWORD='root'
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
    return render_template('status.html', state=state, time=time, **get_latest_sensor_data())


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

    # If it is now closed, open it.

    try:
        if not state['open']:
            open_window()
            flash_text = 'Your window is now open.'
        else:
            close_window()
            flash_text = 'Your window is now closed.'
        flash(flash_text, 'success')
    except Exception as e:
        flash(e.message, "danger")
    return redirect(url_for('index'))


MAX_SENSORDATA_ROWS = 100
@app.route('/api/weather_sensor_data', methods=['POST'])
def post_sensor_data():
    weather = request.get_json()

    db = get_db()
    count = query_db("select count(*) from sensordata", one=True)['count(*)']
    # delete rows in sensordata table if row count exceeds MAX_SENSORDATA_ROWS
    if count >= MAX_SENSORDATA_ROWS:
        db.execute("DELETE FROM sensordata WHERE timestamp IN "
                   "(SELECT timestamp FROM sensordata ORDER BY timestamp LIMIT ?);", [count-MAX_SENSORDATA_ROWS+1])
    db.execute('INSERT INTO sensordata (window_id, wind_angle, wind_speed, temperature, preasure, humidity) '
               'VALUES (?,?,?,?,?,?)', [ACTIVE_WINDOW, weather['wind']['angle'], weather['wind']['speed'], weather['temp'], weather['pressure'], weather['humidity']])
    db.commit()

    return jsonify({'ok': True})


@app.route('/api/weather_data', methods=['get'])
def weather_data():
    return jsonify(get_latest_sensor_data())


@app.route('/configuration', methods=['GET', 'POST'])
@login_required
def configuration():
    if request.method == 'POST':
        db = get_db()
        form = ConfigForm()
        if form.validate_on_submit():
            window_width = form.window_width.data
            window_height = form.window_height.data
            room_area = form.area.data
            window_direction = form.window_direction.data
            room_draft = form.draft.data
            window_hinge = form.window_hinge.data
            db.execute('UPDATE configuration SET width=?, height=?, area=?, hinge=?, angle=?, draftthreshold=? WHERE window_id=?',[window_width, window_height, room_area, window_hinge, window_direction, room_draft, ACTIVE_WINDOW])
            db.commit()
            flash_text = 'Configuration updated'
            flash(flash_text, 'success')
        else:
            flash_text='Invalid input'
            flash(flash_text, 'danger')
    db = get_db()
    config = query_db('SELECT * FROM configuration WHERE window_id=?', [ACTIVE_WINDOW], one=True)
    if config is None:
        flash_text='No configuration set'
        flash(flash_text, 'danger')
        form = ConfigForm()
        return render_template('configuration.html', form=form)
    else:
        window_width_db = config['width']
        window_height_db = config['height']
        room_area_db = config['area']
        window_hinge_db = config['hinge']
        window_direction_db = config['angle']
        room_draft_db = config['draftthreshold']
        form = ConfigForm()
       #form = ConfigForm(window_width=window_width_db, window_height=window_height_db, area=room_area_db, window_direction=window_direction_db, draft=room_draft_db, window_hinge=window_hinge_db)
        return render_template('configuration.html', form = form)


app.wsgi_app = ReverseProxied(app.wsgi_app)

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])

import os
import sqlite3

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

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
        return render_template('status.html', altert='succcess')

    return render_template('status.html') 


@app.route('/configuration')
def configuration():
    return render_template('configuration.html')


app.wsgi_app = ReverseProxied(app.wsgi_app)

if __name__ == '__main__':
    app.run(debug=True)

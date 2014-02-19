from flask import Flask, render_template
from utils import ReverseProxied


app = Flask('webservice')

@app.route('/')
def hello_world():
    return render_template('base.html', test='Testvariael!') 


app.wsgi_app = ReverseProxied(app.wsgi_app)

if __name__ == '__main__':
    app.run(debug=True)

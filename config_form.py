from flask.ext.wtf import Form
from wtforms import TextField, SelectField
from wtforms.validators import NumberRange

class ConfigForm(Form):
    window_width = TextField('window_width', validators = [NumberRange(min=1)])

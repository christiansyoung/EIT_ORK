from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, BooleanField, fields, validators, SelectField


class LoginForm(Form):
    name = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])


class ConfigForm(Form):
    window_width = TextField('window_width', validators = [validators.Regexp('\d+((\.)\d+)?$')])
    window_height = TextField('window_height', validators = [validators.Regexp('\d+((\.)\d+)?$')])
    area = TextField('area', validators = [validators.Regexp('^\d+$')])
    window_direction = SelectField('window_direction', coerce = int, choices = [(0, 'North'), (45, 'North East'), (90, 'East'), (135, 'South East'), (180, 'South'), (225, 'South West'), (270, 'North West')])
    draft = TextField('draft', validators = [validators.Regexp('^\d+((,|\.)\d+)?$')])
    window_hinge = SelectField('window_hinge', coerce=int, choices = [(1, 'Left'), (2, 'Right')])

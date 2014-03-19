from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, BooleanField, fields, validators



#from app.users.models import User
#from app import db

class LoginForm(Form):
    name = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

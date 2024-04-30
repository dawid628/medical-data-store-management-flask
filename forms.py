from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField

class LoginForm(FlaskForm):
    name = StringField('User name')
    password = PasswordField('Password')
    remember = BooleanField('Remember me')
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, validators, SelectField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, Length

##### user forms #####
class LoginForm(FlaskForm):
    name = StringField('Nazwa użytkownika')
    password = PasswordField('Hasło')
    remember = BooleanField('Remember me')

class UserForm(FlaskForm):
    name = StringField('Nazwa użytkownika', validators=[DataRequired(), Length(min=4, max=50)])
    first_name = StringField('Imie', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Nazwisko', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Hasło', validators=[DataRequired(), Length(min=5, max=100)])
    hospital_id = SelectField('Wybierz szpital', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Utwórz')

class EditUserForm(FlaskForm):
    name = StringField('Nazwa użytkownika', render_kw={'readonly': True})
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Imie', validators=[DataRequired()])
    last_name = StringField('Nazwisko', validators=[DataRequired()])
    password = PasswordField('Hasło', validators=[DataRequired(), Length(min=5, max=100)])
    hospital_id = SelectField('Wybierz szpital', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Zapisz')    

##### hospital forms #####
class HospitalForm(FlaskForm):
    name = StringField('Nazwa szpitala', validators=[DataRequired(), Length(max=50)])    
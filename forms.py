from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, validators, SelectField, HiddenField, TextAreaField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, Length
from flask_wtf.file import FileField, FileRequired


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
    hospital_id = SelectField('Szpital', validators=[DataRequired()], coerce=int)
    role_id = SelectField('Rola', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Utwórz')

class EditUserForm(FlaskForm):
    name = StringField('Nazwa użytkownika', render_kw={'readonly': True})
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Imie', validators=[DataRequired()])
    last_name = StringField('Nazwisko', validators=[DataRequired()])
    hospital_id = SelectField('Szpital', validators=[DataRequired()], coerce=int)
    role_id = SelectField('Rola', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Zapisz')

class EditDetailsForm(FlaskForm):
    name = StringField('Nazwa użytkownika', render_kw={'readonly': True})
    email = StringField('Email', render_kw={'readonly': True})
    first_name = StringField('Imie', render_kw={'readonly': True})
    last_name = StringField('Nazwisko', render_kw={'readonly': True})
    password = PasswordField('Hasło', validators=[DataRequired(), Length(min=5, max=100)])     
    submit = SubmitField('Zapisz')

##### hospital forms #####
class HospitalForm(FlaskForm):
    name = StringField('Nazwa szpitala', validators=[DataRequired(), Length(max=50)])    

##### role forms #####
class RoleForm(FlaskForm):
    name = StringField('Nazwa roli', validators=[DataRequired(), Length(max=30)])    

##### file forms #####
class CSVUploadForm(FlaskForm):
    description = TextAreaField('Opis', validators=[DataRequired()])
    csv_file = FileField('Wybierz plik CSV', validators=[FileRequired()])
    submit = SubmitField('Dodaj plik CSV')

class DataEditForm(FlaskForm):
    parent_id = HiddenField()
    version = HiddenField()
    csv_file = FileField('Wybierz plik CSV', validators=[DataRequired()])
    submit = SubmitField('Dodaj plik CSV')
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, current_user
from safety import is_safe_url
from forms import LoginForm, UserForm, EditUserForm


app = Flask(__name__)
app.config.from_pyfile('config.cfg')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # wskazuje funkcje z routingu
login_manager.login_message = 'Musisz być zalogowany jako pracownik.'



##### import models after db init #####
from models import User, Hospital



##### func #####
@login_manager.user_loader
def load_user(id):
    return User.query.filter(User.id == id).first() 



##### routing #####

# init function for development usage
@app.route('/init')
def init():
    db.create_all()
    admin = User.query.filter(User.name=='admin').first()
    if admin is None:
        admin = User(id=1, name='admin', password=User.get_hashed_password('admin'),
                     first_name='Dawid', last_name='Metelski', email='dawidmetelski@gmail.com')
        db.session.add(admin)
        db.session.commit()

    return '<h1>Initial configuration done!</h1>'


##### user routing #####
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.name == form.name.data).first()
        if user and User.verify_password(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('index'))  # Przekierowuje do strony głównej po zalogowaniu
    return render_template('login.html', form = form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


##### users management #####
@app.route('/users')
def users():
    users = User.query.all()
    return render_template('users.html', users = users)


@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('Użytkownik został usunięty.', 'success')
    else:
        flash('Użytkownik nie został znaleziony.', 'warning')

    return redirect(url_for('users'))


@app.route('/new_user', methods=['GET', 'POST'])
def new_user():
    form = UserForm()
    if form.validate_on_submit():
        existing_user = User.query.filter((User.name == form.name.data) | (User.email == form.email.data)).first()
        if existing_user:
            if existing_user.name == form.name.data:
                flash('Nazwa użytkownika już istnieje.', 'warning')
            if existing_user.email == form.email.data:
                flash('Email już istnieje w systemie.', 'warning')
            return render_template('new_user.html', form = form)
        new_user = User(
            name=form.name.data, 
            first_name=form.first_name.data,
            last_name=form.last_name.data, 
            email=form.email.data, 
            password=User.get_hashed_password(form.password.data)  # Hashowanie hasła
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Rejestracja zakończona sukcesem!', 'success')
        return redirect(url_for('login'))
    return render_template('new_user.html', form = form)


@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get(user_id)
    form = EditUserForm(obj=user)
    if user:
        if form.validate_on_submit():
            form.populate_obj(user)
            db.session.commit()
            flash('Dane użytkownika zostały zaktualizowane.', 'success')
            return redirect(url_for('edit_user', user_id=user.id))
        return render_template('edit_user.html', form = form, user = user)
    else:
        flash('Nie znaleziono użytkownika o podanym identyfikatorze.', 'warning')
        return redirect(url_for('users'))
    

##### app routing #####
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', current_user = current_user)

# @app.route('/docs')
# @login_required
# def docs():
#     return '<h1>You have access to protected docs</h1>'

# class Vendor(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(50))
#     discount = db.Column(db.Integer)
#     active = db.Column(db.Boolean)

#     products = db.relationship('Product', backref='vendor', lazy='dynamic')

#     def __repr__(self):
#         return 'Vendor: {}/{}' . format(self.id, self.name)

# class Product(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(50))
#     vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'))

#     def __repr__(self):
#         return 'Prod: ({}) {}'.format(self.id, self.name)

if __name__ == '__main__':
    app.run()
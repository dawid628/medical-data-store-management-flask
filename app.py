from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user
from safety import is_safe_url
from forms import LoginForm


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


@app.route('/', methods=['GET', 'POST'])
def index():
    return 'fWorld'


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter(User.name == form.name.data).first()
        if user != None and User.verify_password(user.password, form.password.data):
            login_user(user, remember = form.remember.data)
            
            next = request.args.get('next')
            if next and is_safe_url(next):
                return redirect(next)
            
            return 'jestes zalogowany mistrzu'

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return '<h1>You are logged out</h1>'


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
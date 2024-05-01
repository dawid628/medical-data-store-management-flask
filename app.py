from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from safety import is_safe_url
from forms import LoginForm, UserForm, EditUserForm, HospitalForm, RoleForm
from functools import wraps


app = Flask(__name__)
app.config.from_pyfile('config.cfg')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # wskazuje funkcje z routingu

@login_manager.unauthorized_handler
def unauthorized():
    flash('Aplikacja dostępna tylko dla pracowników.', 'warning')
    return redirect(url_for('login'))


##### import models after db init #####
from models import User, Hospital, Role



##### func #####
@login_manager.user_loader
def load_user(id):
    return User.query.filter(User.id == id).first() 


def is_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Akcja dostępna tylko dla administratorów.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


##### routing #####

# init function for development usage
@app.route('/init')
def init():
    db.create_all()
    admin = User.query.filter(User.name == 'admin', User.is_active == True).first()
    role = Role.query.filter(Role.name == 'Administrator').first()
    
    if role is None:
        role = Role(id = 1, name = 'Administrator')
        db.session.add(role)
        db.session.commit()

    if admin is None:
        admin = User(id=1, name='admin', password=User.get_hashed_password('admin'),
                     first_name='Dawid', last_name='Metelski', email='dawidmetelski@gmail.com', role_id = role.id)
        db.session.add(admin)
        db.session.commit()

    flash('Inicjalizacja pomyślna.', 'success')
    return redirect(url_for('index'))


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
    return render_template('user/login.html', form = form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


##### users management #####
@app.route('/users')
@login_required
@is_admin_required
def users():
    users = User.query.all()
    return render_template('user/users.html', users = users)


@app.route('/delete_user/<int:user_id>')
@login_required
@is_admin_required
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
@login_required
@is_admin_required
def new_user():
    form = UserForm()

    hospitals = Hospital.query.all()
    form.hospital_id.choices = [(hospital.id, hospital.name) for hospital in hospitals]

    roles = Role.query.all()
    form.role_id.choices = [(role.id, role.name) for role in roles]
    if form.validate_on_submit():
        existing_user = User.query.filter((User.name == form.name.data) | (User.email == form.email.data)).first()
        if existing_user:
            if existing_user.name == form.name.data:
                flash('Nazwa użytkownika już istnieje.', 'warning')
            if existing_user.email == form.email.data:
                flash('Email już istnieje w systemie.', 'warning')
            return render_template('user/new_user.html', form = form)
        new_user = User(
            name=form.name.data, 
            first_name=form.first_name.data,
            last_name=form.last_name.data, 
            email=form.email.data, 
            password=User.get_hashed_password(form.password.data),  # Hashowanie hasła
            hospital_id = form.hospital_id.data,
            role_id = form.role_id.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Rejestracja zakończona sukcesem!', 'success')
        return redirect(url_for('login'))
    
    return render_template('user/new_user.html', form = form)


@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@is_admin_required
def edit_user(user_id):
    user = User.query.get(user_id)
    form = EditUserForm(obj=user)

    hospitals = Hospital.query.all()
    form.hospital_id.choices = [(hospital.id, hospital.name) for hospital in hospitals]

    roles = Role.query.all()
    form.role_id.choices = [(role.id, role.name) for role in roles]

    if user:
        if form.validate_on_submit():
            form.populate_obj(user)  # Uaktualnij obiekt użytkownika na podstawie danych z formularza
            db.session.commit()
            flash('Dane użytkownika zostały zaktualizowane.', 'success')
            return redirect(url_for('users', user_id = user.id))
        
        form.hospital_id.default = user.hospital.id
        form.role_id.default = user.role.id
        return render_template('user/edit_user.html', form=form, user_id = user.id)
    else:
        flash('Nie znaleziono użytkownika o podanym identyfikatorze.', 'error')
        return redirect(url_for('users'))
    

@app.route('/change_user_status/<int:user_id>')
@login_required
@is_admin_required
def change_user_status(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_active = not user.is_active
        db.session.commit()
        flash('Status użytkownika został zmieniony.', 'success')
    else:
        flash('Nie znaleziono użytkownika.', 'warning')
    return redirect(url_for('users'))

    

##### hospital management #####
@app.route('/hospitals')
@login_required
@is_admin_required
def hospitals():
    hospitals = Hospital.query.all()
    return render_template('hospital/hospitals.html', hospitals = hospitals)

@app.route('/new_hospital', methods = ['GET', 'POST'])
@login_required
@is_admin_required
def new_hospital():
    form = HospitalForm()
    if form.validate_on_submit():
        existing_hospital = Hospital.query.filter((Hospital.name == form.name.data)).first()
        if existing_hospital:
            flash('Szpital już istnieje.', 'warning')
            return render_template('hospital/new_hospital.html', form = form)
        
        new_hospital = Hospital(
            name = form.name.data, 
        )
        db.session.add(new_hospital)
        db.session.commit()
        flash('Szpital został utworzony.', 'success')
        return redirect(url_for('hospitals'))

    return render_template('hospital/new_hospital.html', form = form)


@app.route('/edit_hospital/<int:hospital_id>', methods=['GET', 'POST'])
@login_required
@is_admin_required
def edit_hospital(hospital_id):
    hospital = Hospital.query.get(hospital_id)
    form = HospitalForm(obj = hospital)
    if form.validate_on_submit():
        form.populate_obj(hospital)  # Uaktualnij obiekt użytkownika na podstawie danych z formularza
        db.session.commit()
        flash('Szpital został zaktualizowany.', 'success')
        return redirect(url_for('hospitals'))
    return render_template('hospital/edit_hospital.html', form = form, hospital = hospital)


@app.route('/delete_hospital/<int:hospital_id>', methods=['GET', 'POST'])
@login_required
@is_admin_required
def delete_hospital(hospital_id):
    hospital = Hospital.query.get(hospital_id)
    if hospital:
        user_with_hospital = User.query.filter_by(hospital_id=hospital_id).first()
        if user_with_hospital:
            flash('Szpital w użyciu, usunięcie niemożliwe.', 'danger')
            return redirect(url_for('hospitals'))
        db.session.delete(hospital)
        db.session.commit()
        flash('Szpital został usunięty.', 'success')
    else:    
        flash('Szpital nie został znaleziony.', 'warning')
    return redirect(url_for('hospitals'))


##### role management #####
@app.route('/new_role', methods=['GET', 'POST'])
@login_required
@is_admin_required
def new_role():
    form = RoleForm()
    if form.validate_on_submit():
        existing_role= Role.query.filter((Role.name == form.name.data)).first()
        if existing_role:
            flash('Rola już istnieje.', 'warning')
            return render_template('role/new_role.html', form = form)
        
        new_role = Role(
            name = form.name.data, 
        )
        db.session.add(new_role)
        db.session.commit()
        flash('Rola została utworzona.', 'success')
        return redirect(url_for('roles'))
    
    return render_template('role/new_role.html', form = form)


@app.route('/roles')
@login_required
@is_admin_required
def roles():
    roles = Role.query.all()
    return render_template('role/roles.html', roles = roles)


@app.route('/edit_role/<int:role_id>', methods=['GET', 'POST'])
@login_required
@is_admin_required
def edit_role(role_id):
    if role_id == 1:
        flash('Nie można edytować roli administratora.', 'warning')
        return redirect(url_for('roles'))
    role = Role.query.get(role_id)
    form = RoleForm(obj = role)
    if form.validate_on_submit():
        form.populate_obj(role)
        db.session.commit()
        flash('Rola została zaktualizowana.', 'success')
        return redirect(url_for('roles'))
    return render_template('role/edit_role.html', form = form, role = role)


@app.route('/delete_role/<int:role_id>', methods=['GET', 'POST'])
@login_required
@is_admin_required
def delete_role(role_id):
    role = Role.query.get(role_id)

    if role_id == 1:
        flash('Nie można usunąć roli administratora.', 'warning')
        return redirect(url_for('roles')) 
    if role:
        user_with_hospital = User.query.filter_by(role_id=role_id).first()
        if user_with_hospital:
            flash('Rola w użyciu, usunięcie niemożliwe.', 'danger')
            return redirect(url_for('roles'))
        db.session.delete(role)
        db.session.commit()
        flash('Rola została usunięta.', 'success')
    else:    
        flash('Rola nie została znaleziona.', 'warning')
    return redirect(url_for('roles'))


##### app routing #####
@app.route('/', methods=['GET', 'POST'])
@login_required
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
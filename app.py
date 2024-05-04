from imports import *


# Konfiguracja aplikacji
app = Flask(__name__)
app.config.from_pyfile('config.cfg')
db = SQLAlchemy(app)


# Zmiany wlasne dla systemu logowania
login_manager = LoginManager(app)
login_manager.login_view = 'login'
@login_manager.unauthorized_handler
def unauthorized():
    flash('Aplikacja dostępna tylko dla pracowników.', 'warning')
    return redirect(url_for('login'))
@login_manager.user_loader
def load_user(id):
    return User.query.filter(User.id == id).first() 

# Importowanie modeli
from models import User, Hospital, Role, History


# Funkcje 
def get_assets_from_api():
    api_url = app.config.get('API_URL')
    api_key = app.config.get('API_KEY')

    headers = {'X-Api-Key': api_key}
    response = requests.get(api_url + '/assets', headers = headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None

def parse_date(date_str):
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError("no valid date format found")

def is_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Akcja dostępna tylko dla administratorów.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# Routing aplikacji
@app.route('/init') # do developmentu
def init():

    db.create_all()
    admin = User.query.filter(User.name == 'admin', User.is_active == True).first()
    role = Role.query.filter(Role.name == 'Administrator').first()
    
    if role is None:
        role = Role(id = 1, name = 'Administrator')
        db.session.add(role)
        db.session.commit()

    if admin is None:
        admin = User(id = 1, name = 'admin', password = User.get_hashed_password('admin'),
                     first_name = 'Dawid', last_name = 'Metelski', email = 'dawidmetelski@gmail.com', role_id = role.id)
        db.session.add(admin)
        db.session.commit()

    flash('Inicjalizacja pomyślna.', 'success')
    return redirect(url_for('index'))


# Routing uzytkownikow
@app.route('/login', methods = ['GET', 'POST'])
def login():    

    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.name == form.name.data).first()

        if user and User.verify_password(user.password, form.password.data):

            if not user.is_active:
                flash("Twoje konto jest zablokowane.", 'warning')
                return render_template('user/login.html', form = form)
            
            login_user(user, remember = form.remember.data)
            next_page = request.args.get('next')

            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            
            return redirect(url_for('index'))
        
    return render_template('user/login.html', form = form)


@app.route('/logout')
def logout():

    logout_user()
    return redirect(url_for('login'))


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
            name = form.name.data, 
            first_name = form.first_name.data,
            last_name = form.last_name.data, 
            email = form.email.data, 
            password = User.get_hashed_password(form.password.data),  # Hashowanie hasła
            hospital_id = form.hospital_id.data,
            role_id = form.role_id.data
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Rejestracja zakończona sukcesem!', 'success')
        return redirect(url_for('login'))
    
    return render_template('user/new_user.html', form = form)


@app.route('/edit_user/<int:user_id>', methods = ['GET', 'POST'])
@login_required
def edit_user(user_id):

    user = User.query.get(user_id)

    if not current_user.is_admin() and not current_user.id == user_id:
        flash('Musisz być administratorem lub właścicielem konta.', 'warning')
        return redirect(url_for('index'))
    
    if current_user.is_admin():
        form = EditUserForm(obj = user)
        
        hospitals = Hospital.query.all()
        form.hospital_id.choices = [(hospital.id, hospital.name) for hospital in hospitals]

        roles = Role.query.all()
        form.role_id.choices = [(role.id, role.name) for role in roles]
        
        form.hospital_id.default = user.hospital.id if user.hospital else hospitals[0].id
        form.role_id.default = user.role.id
    else:
        form = EditDetailsForm(obj = user)    
    
    if user:
        if form.validate_on_submit():
            form.populate_obj(user)  # Uaktualnij obiekt użytkownika na podstawie danych z formularza
            if current_user.id == user_id and hasattr(form, 'password') and form.password.data is not None:
                user.password = User.get_hashed_password(form.password.data)

            db.session.commit()
            flash('Dane użytkownika zostały zaktualizowane.', 'success')
            return redirect(url_for('index'))
        
        return render_template('user/edit_user.html', form = form, user_id = user.id)
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


# Routing dla szpitali
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


@app.route('/edit_hospital/<int:hospital_id>', methods = ['GET', 'POST'])
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


@app.route('/delete_hospital/<int:hospital_id>', methods = ['GET', 'POST'])
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


# Routing dla ról
@app.route('/new_role', methods = ['GET', 'POST'])
@login_required
@is_admin_required
def new_role():

    form = RoleForm()

    if form.validate_on_submit():
        existing_role = Role.query.filter((Role.name == form.name.data)).first()
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


@app.route('/edit_role/<int:role_id>', methods = ['GET', 'POST'])
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


@app.route('/delete_role/<int:role_id>', methods = ['GET', 'POST'])
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


# Routing aplikacji
@app.route('/', methods = ['GET', 'POST'])
def index():
    return render_template('index.html', current_user = current_user)


@app.route('/new_data', methods = ['GET', 'POST'])
@login_required
def new_data():

    form = CSVUploadForm()

    if form.validate_on_submit():
        file = form.csv_file.data
        description = form.description.data
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')  # Utworzenie znacznika czasu
        filename = secure_filename(f"{timestamp}_{file.filename}")
        file.save(os.path.join('files', filename))

        # Zapis do historii
        dateNow = datetime.now()
        history = History(user_id = current_user.id, filename = filename, date = dateNow, hospital_id = current_user.hospital.id)
        db.session.add(history)
        db.session.commit()

        # Odczyt pliku CSV i przetworzenie wierszy
        csv_file_path = os.path.join('files', filename)
        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                # Konwersja pojedynczego wiersza do formatu JSON
                json_data = json.dumps([row])

                # Przygotowanie danych do wysłania
                UserId = current_user.id
                random_numbers = ''.join([str(random.randint(0, 9)) for _ in range(3)])
                ID = f"{timestamp}{UserId}{random_numbers}"
                FirstName = current_user.first_name
                LastName = current_user.last_name
                Hospital = current_user.hospital.name

                payload = {
                    "ID": ID,
                    "UserId": UserId,
                    "FirstName": FirstName,
                    "LastName": LastName,
                    "Hospital": Hospital,
                    "Data": json_data,
                    "ParentId": None,
                    "Version": 1,
                    "Description": description
                }

                # Wysłanie żądania POST z nagłówkiem X-Api-Key do autoryzacji
                api_url = app.config.get('API_URL')
                api_key = app.config.get('API_KEY')
                headers = {'X-Api-Key': api_key}
                response = requests.post(api_url + '/assets', data=payload, headers=headers)

                # Obsługa odpowiedzi z serwera
                if response.status_code != 202:
                    flash('Nie udało się zapisać danych. Spróbuj ponownie później.', 'warning')
                    flash(f'Odpowiedź serwera: {response.text}', 'warning')
                    return redirect(url_for('new_data'))

        flash('Pliki CSV zostały dodane i wczytane.', 'success')
        return redirect(url_for('new_data'))

    return render_template('data/new_data.html', form=form)


@app.route('/data_history')
@login_required
def data_history():

    history = History.query.all()
    return render_template('data/history.html', history = history)


@app.route('/assets')
@login_required
def get_assets():

    filter_first_name = request.args.get('filter_first_name')
    filter_last_name = request.args.get('filter_last_name')
    filter_hospital = request.args.get('filter_hospital')
    show_deleted = request.args.get('show_deleted') == 'on' 
    
    assets = get_assets_from_api()
    if assets:
        filtered_assets = assets
        
        if filter_first_name:
            filtered_assets = [asset for asset in filtered_assets if asset['FirstName'] == filter_first_name]
        
        if filter_last_name:
            filtered_assets = [asset for asset in filtered_assets if asset['LastName'] == filter_last_name]
        
        if filter_hospital:
            filtered_assets = [asset for asset in filtered_assets if asset['Hospital'] == filter_hospital]
        
        if not show_deleted:
            filtered_assets = [asset for asset in filtered_assets if not asset['IsDeleted']]

        filtered_assets.sort(key=lambda x: parse_date(x['CreatedAt']), reverse=True)
        return render_template('assets/assets.html', assets = filtered_assets)
    else:
        flash('Nie udało się pobrać danych z API.', 'error')
        return redirect(url_for('index'))


@app.route('/export_csv')
@login_required
def export_csv():

    assets = get_assets_from_api()

    if assets:
        # Zapisz dane z assets do pliku CSV w pamięci
        csv_data = io.StringIO()
        fieldnames = ['Imię', 'Nazwisko', 'Szpital', 'Usunięto', 'Wersja', 'Data dodania', 'Opis', 'Dane']
        writer = csv.DictWriter(csv_data, fieldnames = fieldnames)

        writer.writeheader()

        # Zapisz dane z assets do pliku CSV
        for asset in assets:
            if 'Data' in asset:
                try:
                    data = json.loads(asset['Data'])
                except json.JSONDecodeError:
                    data = {}
            else:
                data = {} 

            for row_data in data:
                row = {
                    'Imię': asset['FirstName'],
                    'Nazwisko': asset['LastName'],
                    'Szpital': asset['Hospital'],
                    'Usunięto': asset['IsDeleted'],
                    'Wersja': asset['Version'],
                    'Data dodania': asset['CreatedAt'],
                    'Opis': asset['Description'],
                    'Dane': row_data
                }
                writer.writerow(row)

        csv_data.seek(0)
        filename = 'exported_data.csv'

        return Response(
            csv_data,
            mimetype="text/csv",
            headers = {
                "Content-Disposition": f"attachment;filename={filename}"
            }
        )

    else:
        flash('Nie udało się pobrać danych z API.', 'error')
        return redirect(url_for('index'))

    
@app.route('/asset_delete/<string:asset_id>', methods = ['POST'])
@login_required
def asset_delete(asset_id):

    api_url = app.config.get('API_URL')

    if current_user.is_authenticated and current_user.is_admin():
        url = f"{api_url}/assets/{asset_id}"

        response = requests.delete(url, headers = {'X-Api-Key': app.config.get('API_KEY')})

        if response.status_code == 202:
            flash('Dane zostały pomyślnie usunięte.', 'success')
        else:
            flash('Nie udało się usunąć danych. Spróbuj ponownie później.', 'warning')
            flash(f'Odpowiedź serwera: {response.text}', 'warning')
    else:
        flash('Brak uprawnień do usuwania danych.', 'warning')

    return redirect(url_for('index'))


@app.route('/asset_edit', methods = ['GET', 'POST'])
@login_required
def asset_edit():

    asset_id = request.args.get('asset_id')
    asset_version = request.args.get('asset_version')
    form = CSVUploadForm()

    if form.validate_on_submit():
        file = form.csv_file.data
        parent_id = asset_id
        version = int(asset_version) + 1
        description = form.description.data
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = secure_filename(f"{timestamp}_{file.filename}")
        file.save(os.path.join('files', filename))

        csv_file_path = os.path.join('files', filename)
        data = []
        with open(csv_file_path, 'r', encoding = 'utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                data.append(row)

        json_data = json.dumps(data)
        UserId = current_user.id
        random_numbers = ''.join([str(random.randint(0, 9)) for _ in range(3)])
        ID = f"{timestamp}{UserId}{random_numbers}"
        FirstName = current_user.first_name
        LastName = current_user.last_name
        Hospital = current_user.hospital.name

        payload = {
            "ID": ID,
            "UserId": UserId,
            "FirstName": FirstName,
            "LastName": LastName,
            "Hospital": Hospital,
            "Data": json_data,
            "ParentId": parent_id,
            "Version": version,
            "Description": description
        }

        api_url = app.config.get('API_URL')
        api_key = app.config.get('API_KEY')
        headers = {'X-Api-Key': api_key}
        response = requests.post(api_url + '/assets', data = payload, headers = headers)

        if response.status_code == 202:
            flash('Plik CSV został dodany i wczytany.', 'success')
        else:
            flash('Nie udało się zapisać danych. Spróbuj ponownie później.', 'warning')
            flash(f'Odpowiedź serwera: {response.text}', 'warning')

        return redirect(url_for('get_assets'))

    return render_template('data/edit_data.html', form = form, asset_id = asset_id, asset_version = asset_version)


@app.route('/assets/history/<string:asset_id>') 
@login_required
def asset_history(asset_id):

    all_assets = get_assets_from_api()

    if not all_assets:
        return jsonify({'error': 'Nie udało się pobrać danych z API'}), 500
    
    main_asset = next((a for a in all_assets if a['ID'] == asset_id), None)

    if not main_asset:
        return jsonify({'error': 'Nie znaleziono assetu o podanym ID'}), 404

    versions = [main_asset]  # Rozpocznij listę wersji od głównego assetu
    parent_id = main_asset.get('ParentId')

    while parent_id:
        parent_asset = next((a for a in all_assets if a['ID'] == parent_id), None)
        if parent_asset:
            versions.append(parent_asset)
            parent_id = parent_asset.get('ParentId')
        else:
            print(f"No more parents found starting from parent ID {parent_id}")  # Koniec łańcucha parentów
            break

    versions.reverse()
    return jsonify(versions)



if __name__ == '__main__':
    app.run(debug=True)
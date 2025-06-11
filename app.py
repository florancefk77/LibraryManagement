from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import os
import subprocess
import sys

app = Flask(__name__)  # type: ignore
app.config['APP_NAME'] = os.environ.get('APP_NAME', 'LibraryManagement')
app.secret_key = 'book'

DATA_DIR = 'data'
USERS_FILE = f'{DATA_DIR}/users.csv'
BOOKS_FILE = f'{DATA_DIR}/books.csv'

def initialize_app():
    app = Flask(__name__)
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
        "SESSION_TYPE": "filesystem",
        "DATA_DIR": "test_data",
        "USERS_FILE": "test_data/users.csv",
        "BOOKS_FILE": "test_data/books.csv"
    })
    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
    if not os.path.exists(app.config["USERS_FILE"]):
        pd.DataFrame(columns=['id', 'name', 'email', 'password', 'role']).to_csv(app.config["USERS_FILE"], index=False)
    if not os.path.exists(app.config["BOOKS_FILE"]):
        pd.DataFrame(columns=['id', 'title', 'author', 'year', 'status']).to_csv(app.config["BOOKS_FILE"], index=False)
    return app

def get_users():
    return pd.read_csv(USERS_FILE)

def get_books():
    return pd.read_csv(BOOKS_FILE)

def save_users(df):
    df.to_csv(USERS_FILE, index=False)

def save_books(df):
    df.to_csv(BOOKS_FILE, index=False)

@app.route('/')
def index():
    books = get_books()
    return render_template('index.html', books=books)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        users = get_users()
        if email in users['email'].values:
            flash('Diese E-Mail-Adresse ist bereits registriert.', 'danger')
            return redirect(url_for('register'))
        new_id = int(users['id'].max()) + 1 if not users.empty else 1
        new_user = {'id': new_id, 'name': name, 'email': email, 'password': password, 'role': role}
        users = pd.concat([users, pd.DataFrame([new_user])], ignore_index=True)
        save_users(users)
        flash('Registrierung erfolgreich!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = get_users()
        user = users[users['email'] == email]
        if not user.empty:
            idx = user.index[0]
            if users.loc[idx, 'password'] == password:
                session['user_id'] = int(users.loc[idx, 'id'])
                session['user_name'] = users.loc[idx, 'name']
                session['role'] = users.loc[idx, 'role']
                flash('Willkommen zurück!', 'success')
                if session['role'] == 'admin':
                    return redirect(url_for('admin_users'))
                elif session['role'] == 'staff':
                    return redirect(url_for('books'))
                else:
                    return redirect(url_for('index'))
        flash('Falsche E-Mail oder Passwort.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sie wurden erfolgreich ausgeloggt.', 'success')
    return redirect(url_for('index'))

@app.route('/books', methods=['GET', 'POST'])
def books():
    if 'user_id' not in session or session.get('role') != 'staff':
        flash('Zugriff nicht erlaubt.', 'danger')
        return redirect(url_for('login'))
    books = get_books()
    return render_template('books.html', books=books)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'user_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        year = request.form['year']
        books = get_books()
        new_id = books['id'].max() + 1 if not books.empty else 1
        new_book = {'id': new_id, 'title': title, 'author': author, 'year': year, 'status': 'available'}
        books = pd.concat([books, pd.DataFrame([new_book])], ignore_index=True)
        save_books(books)
        flash('Buch wurde hinzugefügt.', 'success')
        return redirect(url_for('books'))
    return render_template('add_edit_book.html', book=None, action='Neues Buch')

@app.route('/users')
def admin_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Admin-Zugriff erforderlich.', 'danger')
        return redirect(url_for('login'))
    users = get_users()
    books=get_books()
    return render_template('admin_users.html', users=users)

@app.route('/admin/add_user', methods=['GET', 'POST'])
def add_user():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        users = get_users()
        if email in users['email'].values:
            flash('E-Mail bereits vorhanden.', 'danger')
            return redirect(url_for('add_user'))
        new_id = int(users['id'].max()) + 1 if not users.empty else 1
        new_user = {'id': new_id, 'name': name, 'email': email, 'password': password, 'role': role}
        users = pd.concat([users, pd.DataFrame([new_user])], ignore_index=True)
        save_users(users)
        flash('Benutzer hinzugefügt.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('add_edit_user.html',user=None)


@app.route('/admin/edit_user/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    users = get_users()
    user = users[users['id'] == id]

    if user.empty:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_users'))

    idx = user.index[0]

    if request.method == 'POST':
        users.loc[idx, 'name'] = request.form['name']
        users.loc[idx, 'email'] = request.form['email']
        users.loc[idx, 'password'] = request.form['password']
        users.loc[idx, 'role'] = request.form['role']
        save_users(users)
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin_users'))

    return render_template('add_edit_user.html', user=users.loc[idx].to_dict(), action='Edit')


@app.route('/admin/delete_user/<int:id>')
def delete_user(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    users = get_users()
    if id not in users['id'].values:
        flash('Benutzer nicht gefunden.', 'danger')
        return redirect(url_for('admin_users'))
    users = users[users['id'] != id]
    save_users(users)
    flash('Benutzer gelöscht.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/edit_book/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    if 'user_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('login'))
    books = get_books()
    book = books[books['id'] == id]
    if book.empty:
        flash('Das Buch wurde nicht gefunden.', 'danger')
        return redirect(url_for('books'))
    idx = book.index[0]
    if request.method == 'POST':
        books.loc[idx, 'title'] = request.form['title']
        books.loc[idx, 'author'] = request.form['author']
        books.loc[idx, 'year'] = request.form['year']
        books.loc[idx, 'status'] = 'available'
        save_books(books)
        flash('Das Buch wurde erfolgreich aktualisiert.', 'success')
        return redirect(url_for('books'))
    return render_template('add_edit_book.html', book=books.loc[idx], action='Bearbeiten')

@app.route('/delete_book/<int:id>')
def delete_book(id):
    if 'user_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('login'))
    books = get_books()
    if id not in books['id'].values:
        flash('Buch mit dieser ID wurde nicht gefunden.', 'error')
        return redirect(url_for('books'))
    books = books[books['id'] != id]
    save_books(books)
    flash('Buch wurde gelöscht.', 'success')
    return redirect(url_for('books'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = None
    if request.method == 'POST':
        query = request.form['query']
        books = get_books()
        results = books[books['title'].str.contains(query, case=False)]
    return render_template('search.html', results=results)

@app.route('/borrow/<int:id>')
def borrow(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    books = get_books()
    idx = books[books['id'] == id].index
    if not idx.empty:
        if books.loc[idx[0], 'status'] == 'available':
            books.loc[idx[0], 'status'] = 'borrowed'
            save_books(books)
            flash('Buch wurde ausgeliehen.', 'success')
        else:
            flash('Dieses Buch ist bereits ausgeliehen.', 'danger')
    return redirect(url_for('index'))

@app.route('/return/<int:id>')
def return_book(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    books = get_books()
    idx = books[books['id'] == id].index
    if not idx.empty:
        if books.loc[idx[0], 'status'] == 'borrowed':
            books.loc[idx[0], 'status'] = 'available'
            save_books(books)
            flash('Buch wurde zurückgegeben.', 'success')
        else:
            flash('Dieses Buch wurde noch nicht ausgeliehen.', 'danger')
    return redirect(url_for('index'))


# install all packages 
def install_packages():
    # List of packages to install
    packages = [
        'pip',  # First upgrade pip
        'flask',
        'pandas',
        'pytest'
    ]
    
    try:
        # Upgrade pip first
        print("Upgrading pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        
        # Install remaining packages
        for package in packages[1:]:  # Skip pip since we already upgraded it
            print(f"Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
            print(f"{package} installed successfully!")
            
        print("\nAll packages installed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        print("Please run the application with administrator privileges.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == '__main__':
  #  print("Initializing application...") 
   # install_packages()
    initialize_app()
    app.run(debug=True)
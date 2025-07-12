from flask import Flask, render_template, request, jsonify, session, g
import os
import json
import sqlite3

app = Flask(__name__)

app.secret_key = os.urandom(24)   # Needed for session to work

DATABASE = 'data.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                submit TEXT
            )
        ''')
        db.commit()

@app.route('/')
def login():
    return render_template('login.html')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/catch', methods=['POST'])
def catch():
    data = request.get_json()
    if 'name' in data and 'email' in data and 'password' in data and 'submit' in data:
        name = data['name']
        email = data['email']
        password = data['password']
        submit = data['submit']
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (name, email, password, submit) 
                VALUES (?, ?, ?, ?)
            ''', (name, email, password, submit))
            db.commit()
            return jsonify({'status': 'success', 'message': 'Data saved in SQLite!'})
        except sqlite3.IntegrityError:
            print("Email already exists!")
            return jsonify({'status': 'error', 'message': 'Email already exists!'}), 400
    else:
        return jsonify({'status': 'error', 'message': 'Invalid data!'}), 400

@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    if 'email' in data and 'password' in data:
        email = data['email']
        password = data['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT * FROM users WHERE email=? AND password=?
        ''', (email, password))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user[0]
            return jsonify({'status': 'success', 'message': 'Login successful!'})
        else:
            print("Invalid credentials!")
            return jsonify({'status': 'error', 'message': 'Invalid credentials!'}), 401
    else:
        print("Invalid data!")
        return jsonify({'status': 'error', 'message': 'Invalid data!'}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

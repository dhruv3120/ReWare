from flask import Flask, request, jsonify, render_template, session, g
from flask_cors import CORS
import sqlite3
import hashlib
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Replace with a strong secret
CORS(app)

DATABASE = 'data.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize DB tables if not exist
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
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
        
        # Create users table with all required columns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                full_name TEXT,
                points INTEGER DEFAULT 0
            )
        ''')
        
        # Create user_items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_email TEXT NOT NULL,
                category TEXT NOT NULL,
                item_name TEXT NOT NULL,
                item_points INTEGER NOT NULL,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create swap_requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS swap_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                item_name TEXT NOT NULL,
                item_points INTEGER NOT NULL,
                phone TEXT,
                address TEXT,
                pincode TEXT,
                swap_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        db.commit()

# ---------- Routes ----------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/catch', methods=['POST'])
def catch():
    data = request.get_json()
    if 'name' in data and 'email' in data and 'password' in data and 'submit' in data:
        name = data['name']
        email = data['email'].lower()
        password = data['password']
        
        # Hash the password before storing
        hashed_password = hash_password(password)
        
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (name, email, password, full_name, points) 
                VALUES (?, ?, ?, ?, ?)
            ''', (name, email, hashed_password, name, 0))
            db.commit()
            return jsonify({'status': 'success', 'message': 'Data saved in SQLite!'})
        except sqlite3.IntegrityError:
            print("Email already exists!")
            return jsonify({'status': 'error', 'message': 'Email already exists!'}), 400
    else:
        return jsonify({'status': 'error', 'message': 'Invalid data!'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Missing fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower(),))
    user = cursor.fetchone()
    conn.close()
    
    if user and user['password'] == hash_password(password):
        session['user_email'] = email.lower()
        return jsonify({
            'email': user['email'],
            'fullName': user['full_name'] or user['name'],
            'points': user['points']
        })
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_email', None)
    return jsonify({'message': 'Logged out'})

@app.route('/api/user', methods=['GET'])
def get_user():
    email = session.get('user_email')
    if not email:
        return jsonify({'error': 'Not authenticated'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, full_name, email, points FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            'email': user['email'], 
            'fullName': user['full_name'] or user['name'], 
            'points': user['points']
        })
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/api/categories', methods=['GET'])
def categories():
    # Static + user items combined
    static_items = {
        "Men's Wear": [
            {"name": "Denim Jacket", "points": 5, "image": "https://i.imgur.com/LN0YUN2.jpg"},
            {"name": "Leather Boots", "points": 10, "image": "https://i.imgur.com/NnKPhXJ.jpg"}
        ],
        "Women's Wear": [
            {"name": "Red Saree", "points": 5, "image": "https://i.imgur.com/LZoZfD7.jpg"},
            {"name": "Designer Kurti", "points": 10, "image": "https://i.imgur.com/39sX3jz.jpg"}
        ],
        "Kids Wear": [
            {"name": "Cartoon Shirt", "points": 10, "image": "https://i.imgur.com/vMZ8GKR.jpg"}
        ],
        "For Gen Z": [
            {"name": "Oversized Hoodie", "points": 12, "image": "https://i.imgur.com/O9KfGVG.jpg"}
        ],
        "For Millennials": [
            {"name": "Formal Shirt", "points": 10, "image": "https://i.imgur.com/jIPyJ6G.jpg"}
        ]
    }

    email = session.get('user_email')
    if email:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT category, item_name, item_points, image_url FROM user_items WHERE owner_email=?", (email,))
        user_items = cursor.fetchall()
        conn.close()
        
        for item in user_items:
            cat = item['category']
            if cat not in static_items:
                static_items[cat] = []
            static_items[cat].append({
                "name": item['item_name'],
                "points": item['item_points'],
                "image": item['image_url']
            })

    return jsonify(static_items)

@app.route('/api/upload_item', methods=['POST'])
def upload_item():
    email = session.get('user_email')
    if not email:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    name = data.get('name')
    category = data.get('category')
    image_url = data.get('imageUrl')

    if not name or not category or not image_url:
        return jsonify({'error': 'Missing fields'}), 400

    # Estimate points based on name length
    length = len(name.strip())
    if length <= 5:
        points = 5
    elif length <= 10:
        points = 10
    else:
        points = 12

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_items (owner_email, category, item_name, item_points, image_url) VALUES (?, ?, ?, ?, ?)",
        (email, category, name, points, image_url)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Item uploaded successfully'})

@app.route('/api/swap', methods=['POST'])
def swap():
    email = session.get('user_email')
    if not email:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.json
    item_name = data.get('itemName')
    item_points = data.get('itemPoints')
    phone = data.get('phone')
    address = data.get('address')
    pincode = data.get('pincode')

    if not all([item_name, item_points, phone, address, pincode]):
        return jsonify({'error': 'Missing fields'}), 400

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO swap_requests (user_email, item_name, item_points, phone, address, pincode, swap_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (email, item_name, item_points, phone, address, pincode, now)
    )
    cursor.execute(
        "UPDATE users SET points = points + ? WHERE email = ?",
        (item_points, email)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': f'Swapped {item_name} successfully!'})

@app.route('/api/swaps', methods=['GET'])
def get_swaps():
    email = session.get('user_email')
    if not email:
        return jsonify({'error': 'Not authenticated'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT item_name, swap_date FROM swap_requests WHERE user_email=? ORDER BY swap_date DESC",
        (email,)
    )
    swaps = cursor.fetchall()
    conn.close()
    swap_list = [{"itemName": row['item_name'], "swapDate": row['swap_date']} for row in swaps]
    return jsonify(swap_list)

if __name__ == '__main__':
    init_db()  # Initialize database tables
    app.run(debug=True)
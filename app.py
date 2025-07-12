from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import sqlite3
import hashlib
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Replace with a strong secret
CORS(app)

DB = "users.db"

def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize DB tables if not exist
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            points INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS swap_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            item_name TEXT,
            item_points INTEGER,
            phone TEXT,
            address TEXT,
            pincode TEXT,
            swap_date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_email TEXT,
            category TEXT,
            item_name TEXT,
            item_points INTEGER,
            image_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------- Routes ----------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    full_name = data.get('fullName')
    email = data.get('email')
    password = data.get('password')
    if not full_name or not email or not password:
        return jsonify({'error': 'Missing fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (full_name, email, password) VALUES (?, ?, ?)",
            (full_name, email.lower(), hash_password(password))
        )
        conn.commit()
        return jsonify({'message': 'Registered successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 409
    finally:
        conn.close()

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
            'fullName': user['full_name'],
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
    cursor.execute("SELECT full_name, email, points FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({'email': user['email'], 'fullName': user['full_name'], 'points': user['points']})
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
    conn = get_db_connection()
    cursor = conn.cursor()
    if email:
        cursor.execute("SELECT category, item_name, item_points, image_url FROM user_items WHERE owner_email=?", (email,))
        user_items = cursor.fetchall()
        for item in user_items:
            cat = item['category']
            if cat not in static_items:
                static_items[cat] = []
            static_items[cat].append({
                "name": item['item_name'],
                "points": item['item_points'],
                "image": item['image_url']
            })
    conn.close()

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
    app.run(debug=True)

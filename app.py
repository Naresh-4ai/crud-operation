from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = 'secret_key_123'
DB_NAME = "database.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                phone TEXT
            )
        ''')
        conn.commit()

init_db()

# --- PAGE ROUTES ---

@app.route('/')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('home.html')

# --- API ROUTES (Data handling) ---

@app.route('/api/register', methods=['POST'])
def register_api():
    data = request.json
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)",
                           (data['username'], data['password'], data['email'], data['phone']))
            conn.commit()
        return jsonify({"success": True, "message": "Registered successfully! Please login."})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username already taken."})

@app.route('/api/login', methods=['POST'])
def login_api():
    data = request.json
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                       (data['username'], data['password']))
        user = cursor.fetchone()
    
    if user:
        session['user_id'] = user['id']
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid username or password"})

@app.route('/api/user', methods=['GET', 'PUT'])
def user_ops():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']

    if request.method == 'GET':
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT username, email, phone FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
        return jsonify(dict(user))

    if request.method == 'PUT':
        data = request.json
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET email = ?, phone = ? WHERE id = ?", 
                           (data['email'], data['phone'], user_id))
            conn.commit()
        return jsonify({"success": True, "message": "Profile updated!"})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)
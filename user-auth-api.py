# user_auth_api.py
# Test file for CodeRabbit security review capabilities

import mysql.connector
import hashlib
import pickle
import os
from flask import Flask, request, jsonify, session

app = Flask(__name__)
app.secret_key = "my-secret-key-123"  # Hardcoded secret

# Database connection with hardcoded credentials
DB_CONFIG = {
    'host': 'prod.database.com',
    'user': 'admin',
    'password': 'P@ssw0rd123!',  # Hardcoded password
    'database': 'users'
}

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # SQL Injection vulnerability
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    
    if user:
        # Insecure session management
        session['user_id'] = user[0]
        session['is_admin'] = request.form.get('is_admin', False)  # Client-controlled admin flag
        
        # Information disclosure
        return jsonify({
            'success': True,
            'user_id': user[0],
            'api_key': os.environ.get('API_KEY'),  # Leaking API key
            'debug_info': str(user)  # Exposing internal data
        })
    
    # User enumeration vulnerability
    return jsonify({'error': f'User {username} not found'}), 401

@app.route('/reset_password', methods=['POST'])
def reset_password():
    email = request.form.get('email')
    new_password = request.form.get('password')
    
    # Weak password hashing
    hashed = hashlib.md5(new_password.encode()).hexdigest()
    
    # No rate limiting - DoS vulnerability
    # Missing authentication check
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    # Another SQL injection
    cursor.execute(f"UPDATE users SET password='{hashed}' WHERE email='{email}'")
    conn.commit()
    
    # No logging - Repudiation issue
    return jsonify({'success': True})

@app.route('/admin/users', methods=['GET'])
def get_users():
    # Broken access control - no authorization check
    if 'user_id' in session:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        # Unsafe deserialization
        if request.args.get('filter'):
            filter_obj = pickle.loads(request.args.get('filter').encode())
            # Process filter...
        
        return jsonify(users)
    
    return jsonify({'error': 'Not logged in'}), 401

@app.route('/upload', methods=['POST'])
def upload_file():
    # Path traversal vulnerability
    filename = request.form.get('filename')
    content = request.files['file'].read()
    
    # No file validation
    with open(f"/var/uploads/{filename}", 'wb') as f:
        f.write(content)
    
    # Command injection
    os.system(f"virus_scan {filename}")
    
    return jsonify({'uploaded': filename})

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    
    # XSS vulnerability in API response
    return f"<h1>Results for: {query}</h1>"

# Missing: Input validation, CSRF protection, rate limiting, proper logging

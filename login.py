from flask import request, jsonify
import mysql.connector
from werkzeug.security import check_password_hash
from app import get_db_connection  # Assumes get_db_connection is in app.py

def handle_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, password FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and check_password_hash(user['password'], password):
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email']
            }
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401
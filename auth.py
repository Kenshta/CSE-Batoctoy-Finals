from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
import hashlib
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

# Secret key for JWT - in production, use a strong random secret
SECRET_KEY = 'your-super-secret-key-change-this-in-production'

# Database config - should match your main app
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',  # your MySQL password
    'database': 'kenschema'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def hash_password(password):
    """Hash a password for comparing."""
    return hashlib.sha256(password.encode()).hexdigest()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_user_id, *args, **kwargs)
    return decorated

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Hash the provided password for comparison
    hashed_password = hash_password(password)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Find user by username or email
        cursor.execute(
            "SELECT id, username, email, password_hash FROM users WHERE (username = %s OR email = %s) AND password_hash = %s",
            (username, username, hashed_password)
        )
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user['id'],
            'username': user['username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)  # Token expires in 24 hours
        }, SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        }), 200
        
    except Error as e:
        cursor.close()
        conn.close()
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/logout', methods=['POST'])
@token_required
def logout(current_user_id):
    # In a real application with a blacklist, you would add the token here
    # For this simple implementation, we just tell the client to remove the token
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, username, email, created_at FROM users WHERE id = %s",
            (current_user_id,)
        )
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'created_at': user['created_at'].isoformat() if user['created_at'] else None
            }
        }), 200
        
    except Error as e:
        cursor.close()
        conn.close()
        return jsonify({'error': f'Failed to retrieve profile: {str(e)}'}), 500

@app.route('/change-password', methods=['PUT'])
@token_required
def change_password(current_user_id):
    data = request.get_json()
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    confirm_new_password = data.get('confirm_new_password')
    
    if not old_password or not new_password or not confirm_new_password:
        return jsonify({'error': 'Old password, new password, and confirmation are required'}), 400
    
    if new_password != confirm_new_password:
        return jsonify({'error': 'New passwords do not match'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters long'}), 400
    
    # Get current user's hashed password
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT password_hash FROM users WHERE id = %s",
            (current_user_id,)
        )
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        # Verify old password
        if user['password_hash'] != hash_password(old_password):
            cursor.close()
            conn.close()
            return jsonify({'error': 'Incorrect old password'}), 401
        
        # Update password
        new_hashed_password = hash_password(new_password)
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (new_hashed_password, current_user_id)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Error as e:
        cursor.close()
        conn.close()
        return jsonify({'error': f'Password change failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002)  # Different port to avoid conflict
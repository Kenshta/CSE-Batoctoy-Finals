from flask import Flask, jsonify, request, make_response
from config import get_db_connection
import dicttoxml2
from dicttoxml2 import dicttoxml
import pymysql

app = Flask(__name__)

def format_response(data, format_type='json'):
    if format_type == 'xml':
        xml_data = dicttoxml(data, custom_root='response', attr_type=False)
        response = make_response(xml_data)
        response.headers['Content-Type'] = 'application/xml'
    else:
        response = jsonify(data)
    return response

@app.route('/users', methods=['GET'])
def get_users():
    format_type = request.args.get('format', 'json').lower()
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT id, name, email, age FROM users")
    users = cursor.fetchall()
    conn.close()
    return format_response({"users": users}, format_type)

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    format_type = request.args.get('format', 'json').lower()
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT id, name, email, age FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return format_response({"user": user}, format_type)
    else:
        return format_response({"error": "User not found"}, format_type), 404

@app.route('/users', methods=['POST'])
def create_user():
    format_type = request.args.get('format', 'json').lower()
    data = request.get_json()
    if not data or not all(k in data for k in ("name", "email", "age")):
        return format_response({"error": "Invalid input"}, format_type), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, age) VALUES (%s, %s, %s)",
            (data['name'], data['email'], data['age'])
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return format_response({"message": "User created", "id": user_id}, format_type), 201
    except pymysql.IntegrityError:
        conn.close()
        return format_response({"error": "Email must be unique"}, format_type), 400

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    format_type = request.args.get('format', 'json').lower()
    data = request.get_json()
    if not data:
        return format_response({"error": "No update data provided"}, format_type), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    if not cursor.fetchone():
        conn.close()
        return format_response({"error": "User not found"}, format_type), 404

    fields = []
    params = []
    if 'name' in data:
        fields.append("name = %s")
        params.append(data['name'])
    if 'email' in data:
        fields.append("email = %s")
        params.append(data['email'])
    if 'age' in data:
        fields.append("age = %s")
        params.append(data['age'])

    if not fields:
        conn.close()
        return format_response({"error": "No valid fields to update"}, format_type), 400

    params.append(user_id)
    query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
    try:
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return format_response({"message": "User updated"}, format_type)
    except pymysql.IntegrityError:
        conn.close()
        return format_response({"error": "Email must be unique"}, format_type), 400

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    format_type = request.args.get('format', 'json').lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    if not cursor.fetchone():
        conn.close()
        return format_response({"error": "User not found"}, format_type), 404

    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
    return format_response({"message": "User deleted"}, format_type)
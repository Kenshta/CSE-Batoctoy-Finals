from flask import Flask, request, jsonify, make_response
<<<<<<< HEAD
import MySQLdb
import MySQLdb.cursors
import xml.etree.ElementTree as ET
from xml.dom import minidom

app = Flask(__name__)

# =========================
# Database config
# =========================
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "root"
DB_NAME = "kenschema"

def get_db_connection():
    return MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        cursorclass=MySQLdb.cursors.DictCursor
    )

def get_cursor():
    conn = get_db_connection()
    return conn, conn.cursor()

# =========================
# Safe request reader
# =========================
def get_request_data():
    return request.get_json(silent=True) or {}

# =========================
# Response format
# =========================
def get_format():
    fmt = request.args.get("format", "json").lower()
    return "xml" if fmt == "xml" else "json"

# =========================
# XML converter
# =========================
def users_to_xml(users):
    root = ET.Element("users")
    for u in users:
        user = ET.SubElement(root, "user")
        ET.SubElement(user, "id").text = str(u["id"])
        ET.SubElement(user, "name").text = u["name"]
        ET.SubElement(user, "email").text = u["email"]
        ET.SubElement(user, "age").text = str(u["age"]) if u["age"] else ""
    rough = ET.tostring(root, "utf-8")
    return minidom.parseString(rough).toprettyxml(indent="  ")

def format_response(data):
    fmt = get_format()
    if fmt == "xml":
        xml = users_to_xml(data if isinstance(data, list) else [data])
        res = make_response(xml)
        res.headers["Content-Type"] = "application/xml"
        return res
    return jsonify(data)

# =========================
# CREATE user
# =========================
@app.route("/users", methods=["POST"])
def create_user():
    data = get_request_data()
    name = data.get("name")
    email = data.get("email")
    age = data.get("age")

    if not name or not email:
        return jsonify({"error": "name and email required"}), 400

    conn, cur = get_cursor()
    try:
        cur.execute(
            "INSERT INTO users (name, email, age) VALUES (%s,%s,%s)",
            (name, email, age)
        )
        conn.commit()
        user = {
            "id": cur.lastrowid,
            "name": name,
            "email": email,
            "age": age
        }
        return format_response(user), 201
    except MySQLdb.IntegrityError:
        return jsonify({"error": "email already exists"}), 409
    finally:
        cur.close()
        conn.close()

# =========================
# READ all users
# =========================
@app.route("/users", methods=["GET"])
def get_users():
    conn, cur = get_cursor()
    try:
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        return format_response(users)
    finally:
        cur.close()
        conn.close()

# =========================
# READ one user
# =========================
@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn, cur = get_cursor()
    try:
        cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404
        return format_response(user)
    finally:
        cur.close()
        conn.close()

# =========================
# UPDATE user
# =========================
@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = get_request_data()

    conn, cur = get_cursor()
    try:
        cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        name = data.get("name", user["name"])
        email = data.get("email", user["email"])
        age = data.get("age", user["age"])

        cur.execute(
            "UPDATE users SET name=%s, email=%s, age=%s WHERE id=%s",
            (name, email, age, user_id)
        )
        conn.commit()

        updated = {
            "id": user_id,
            "name": name,
            "email": email,
            "age": age
        }
        return format_response(updated)
    except MySQLdb.IntegrityError:
        return jsonify({"error": "email already exists"}), 409
    finally:
        cur.close()
        conn.close()

# =========================
# DELETE user
# =========================
@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    conn, cur = get_cursor()
    try:
        cur.execute("SELECT id FROM users WHERE id=%s", (user_id,))
        if not cur.fetchone():
            return jsonify({"error": "User not found"}), 404

        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
        return jsonify({"message": "User deleted"})
    finally:
        cur.close()
        conn.close()

# =========================
# ROOT
# =========================
@app.route("/")
def index():
    return jsonify({"status": "CSE1 CRUD API running"})

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
=======
import mysql.connector
from mysql.connector import Error
import xml.etree.ElementTree as ET
from xml.dom import minidom
from werkzeug.security import check_password_hash  # ✅ Import at top

app = Flask(__name__)

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',          # Update if needed
    'database': 'testdb'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def user_to_xml(users):
    root = ET.Element("users")
    for user in users:
        user_elem = ET.SubElement(root, "user")
        ET.SubElement(user_elem, "id").text = str(user['id'])
        ET.SubElement(user_elem, "name").text = user['name']
        ET.SubElement(user_elem, "email").text = user['email']
        ET.SubElement(user_elem, "age").text = str(user['age']) if user['age'] else ''
    rough = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough)
    return reparsed.toprettyxml(indent="  ")

def get_format():
    fmt = request.args.get('format', 'json').lower()
    if fmt not in ['json', 'xml']:
        fmt = 'json'
    return fmt

# Helper to fetch all users
def fetch_all_users():
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

# Helper to fetch user by ID
def fetch_user_by_id(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

# CREATE
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    age = data.get('age')

    if not name or not email:
        return jsonify({'error': 'Name and email required'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, age) VALUES (%s, %s, %s)",
            (name, email, age)
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()

        new_user = {'id': user_id, 'name': name, 'email': email, 'age': age}
        fmt = get_format()
        if fmt == 'xml':
            xml_str = user_to_xml([new_user])
            response = make_response(xml_str)
            response.headers['Content-Type'] = 'application/xml'
            return response
        else:
            return jsonify(new_user), 201
    except mysql.connector.IntegrityError:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Email already exists'}), 409

# READ all
@app.route('/users', methods=['GET'])
def get_users():
    users = fetch_all_users()
    fmt = get_format()
    if fmt == 'xml':
        xml_str = user_to_xml(users)
        response = make_response(xml_str)
        response.headers['Content-Type'] = 'application/xml'
        return response
    else:
        return jsonify(users)

# READ one
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = fetch_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    fmt = get_format()
    if fmt == 'xml':
        xml_str = user_to_xml([user])
        response = make_response(xml_str)
        response.headers['Content-Type'] = 'application/xml'
        return response
    else:
        return jsonify(user)

# UPDATE
@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = fetch_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    name = data.get('name', user['name'])
    email = data.get('email', user['email'])
    age = data.get('age', user['age'])

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET name = %s, email = %s, age = %s WHERE id = %s",
            (name, email, age, user_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        updated_user = {'id': user_id, 'name': name, 'email': email, 'age': age}
        fmt = get_format()
        if fmt == 'xml':
            xml_str = user_to_xml([updated_user])
            response = make_response(xml_str)
            response.headers['Content-Type'] = 'application/xml'
            return response
        else:
            return jsonify(updated_user)
    except mysql.connector.IntegrityError:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Email already exists'}), 409

# DELETE
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = fetch_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'User deleted'}), 200

# LOGIN
@app.route('/auth/login', methods=['POST'])
def login():
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

    if user and user.get('password') and check_password_hash(user['password'], password):
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

# Root endpoint
@app.route('/', methods=['GET'])
def home():
    return "CSE1 CRUD API — Use /users or /auth/login"

if __name__ == '__main__':
    app.run(debug=True)
>>>>>>> d617b91176ef03d8f0ea4c614e668b72c2683591

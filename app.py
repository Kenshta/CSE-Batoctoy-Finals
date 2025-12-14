from flask import Flask, request, jsonify, make_response
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

from flask import Flask, jsonify, request, make_response
from flask_mysqldb import MySQL

app = Flask(__name__)

# MySQL Config (update with your local DB)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # your MySQL password
app.config['MYSQL_DB'] = 'my_app_db'  # your DB name

mysql = MySQL(app)

# Example: GET all users
@app.route('/users', methods=['GET'])
def get_users():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, email FROM users")
    users = cur.fetchall()
    cur.close()

    return jsonify([
        {'id': u[0], 'name': u[1], 'email': u[2]} for u in users
    ])

# Example: POST a new user
@app.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    name = data['name']
    email = data['email']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
    mysql.connection.commit()
    cur.close()

    return make_response(jsonify({'message': 'User created'}), 201)

# Home route
@app.route('/')
def home():
    return jsonify({'message': 'Flask REST API is running!'})

if __name__ == '__main__':
    app.run(debug=True)
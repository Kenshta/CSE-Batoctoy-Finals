from flask import Flask, request, jsonify, make_response, render_template_string
from flask_bcrypt import Bcrypt
from functools import wraps
import datetime
import jwt
import xmltodict
import importlib
import os

# ----------------------------------
# APP SETUP
# ----------------------------------
app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config["SECRET_KEY"] = "supersecretkey"
app.config["JWT_EXP_HOURS"] = 2

# ----------------------------------
# DATABASE (MySQL with SQLite fallback)
# ----------------------------------
mysql_connector = None
try:
    mysql_connector = importlib.import_module("mysql.connector")
    MYSQL_AVAILABLE = True
except Exception:
    MYSQL_AVAILABLE = False

if MYSQL_AVAILABLE:
    db = mysql_connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="library_db"
    )
    cursor = db.cursor(dictionary=True)
else:
    import sqlite3
    conn = sqlite3.connect("library.sqlite3", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    raw = conn.cursor()

    class Cursor:
        def execute(self, sql, params=()):
            raw.execute(sql.replace("%s", "?"), params)

        def fetchone(self):
            row = raw.fetchone()
            return dict(row) if row else None

        def fetchall(self):
            return [dict(r) for r in raw.fetchall()]

    cursor = Cursor()
    db = conn

    raw.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    raw.execute("""
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            genre TEXT,
            publish_year INTEGER,
            isbn TEXT,
            available_copies INTEGER,
            date_added TEXT
        )
    """)
    conn.commit()

def seed_books():
    cursor.execute("SELECT COUNT(*) AS total FROM books")
    result = cursor.fetchone()

    # for SQLite fallback compatibility
    total = list(result.values())[0] if isinstance(result, dict) else result[0]

    if total > 0:
        return  # already seeded

    books = [
    ("The Great Gatsby", "F. Scott Fitzgerald", "Fiction", 1925, "9780743273565", 5),
    ("1984", "George Orwell", "Dystopian", 1949, "9780451524935", 3),
    ("To Kill a Mockingbird", "Harper Lee", "Classic", 1960, "9780061120084", 7),
    ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "Fantasy", 1997, "9780590353427", 10),
    ("The Hobbit", "J.R.R. Tolkien", "Fantasy", 1937, "9780547928227", 4),
    ("Pride and Prejudice", "Jane Austen", "Romance", 1813, "9780141439518", 6),
    ("Moby Dick", "Herman Melville", "Adventure", 1851, "9781503280786", 2),
    ("The Catcher in the Rye", "J.D. Salinger", "Fiction", 1951, "9780316769488", 5),
    ("Brave New World", "Aldous Huxley", "Sci-Fi", 1932, "9780060850524", 3),
    ("The Lord of the Rings", "J.R.R. Tolkien", "Fantasy", 1954, "9780618640157", 8),
    ("The Alchemist", "Paulo Coelho", "Fiction", 1988, "9780061122415", 4),
    ("The Da Vinci Code", "Dan Brown", "Mystery", 2003, "9780307474278", 9),
    ("The Picture of Dorian Gray", "Oscar Wilde", "Classic", 1890, "9780141442464", 5),
    ("The Shining", "Stephen King", "Horror", 1977, "9780307743657", 3),
    ("The Hunger Games", "Suzanne Collins", "Sci-Fi", 2008, "9780439023481", 7),
    ("The Fault in Our Stars", "John Green", "Romance", 2012, "9780525478812", 6),
    ("IT", "Stephen King", "Horror", 1986, "9781501142970", 4),
    ("The Maze Runner", "James Dashner", "Sci-Fi", 2009, "9780385737951", 6),
    ("The Girl on the Train", "Paula Hawkins", "Thriller", 2015, "9781594634024", 5),
    ("The Silent Patient", "Alex Michaelides", "Thriller", 2019, "9781250301697", 4),
]


    for b in books:
        cursor.execute("""
            INSERT INTO books (title, author, genre, publish_year, isbn, available_copies, date_added)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            b[0], b[1], b[2], b[3], b[4], b[5],
            datetime.date.today().isoformat()
        ))

    db.commit()


# ----------------------------------
# JWT DECORATOR
# ----------------------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token missing"}), 401

        try:
            jwt.decode(token.replace("Bearer ", ""), app.config["SECRET_KEY"], algorithms=["HS256"])
        except:
            return jsonify({"error": "Invalid or expired token"}), 401

        return f(*args, **kwargs)
    return decorated

# ----------------------------------
# FORMAT RESPONSE (JSON / XML)
# ----------------------------------
def respond(data):
    fmt = request.args.get("format", "json")
    if fmt == "xml":
        xml = xmltodict.unparse({"response": data}, pretty=True)
        res = make_response(xml)
        res.headers["Content-Type"] = "application/xml"
        return res
    return jsonify(data)

# ----------------------------------
# AUTH ROUTES
# ----------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return """
        <h1>Register</h1>
        <form method="POST">
            <input name="username" placeholder="Username" required><br><br>
            <input name="password" type="password" placeholder="Password" required><br><br>
            <button type="submit">Register</button>
        </form>
        """

    # POST
    data = request.form
    username = data.get("username")
    password = data.get("password")

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        return "User already exists"

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        (username, pw_hash)
    )
    db.commit()

    return "<h3>Registration successful</h3><a href='/login'>Login</a>"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return """
        <h1>Login</h1>
        <form method="POST">
            <input name="username" placeholder="Username" required><br><br>
            <input name="password" type="password" placeholder="Password" required><br><br>
            <button type="submit">Login</button>
        </form>
        """

    # POST
    data = request.form
    username = data.get("username")
    password = data.get("password")

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()

    if not user or not bcrypt.check_password_hash(user["password"], password):
        return "Invalid credentials"

    return "<h3>Login successful</h3><a href='/books'>View Books</a>"


# ----------------------------------
# PUBLIC BOOK VIEW (NO TOKEN)
# ----------------------------------
@app.route("/books")
def books_page():
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    html = """
    <h1>Library Books</h1>
    {% for b in books %}
    <pre>
Book ID: {{b.book_id}}
Title: {{b.title}}
Author: {{b.author}}
Genre: {{b.genre}}
Publish Year: {{b.publish_year}}
ISBN: {{b.isbn}}
Available Copies: {{b.available_copies}}
Date Added: {{b.date_added or 'N/A'}}
-------------------------
    </pre>
    {% endfor %}
    """
    return render_template_string(html, books=books)

# ----------------------------------
# CRUD API (PROTECTED)
# ----------------------------------
@app.route("/api/books", methods=["GET"])
@token_required
def get_books():
    cursor.execute("SELECT * FROM books")
    return respond(cursor.fetchall())

@app.route("/api/books/<int:id>", methods=["GET"])
@token_required
def get_book(id):
    cursor.execute("SELECT * FROM books WHERE book_id=%s", (id,))
    book = cursor.fetchone()
    if not book:
        return jsonify({"error": "Not found"}), 404
    return respond(book)

@app.route("/api/books", methods=["POST"])
@token_required
def add_book():
    data = request.json
    required = ["title", "author", "genre", "publish_year", "isbn", "available_copies"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    cursor.execute("""
        INSERT INTO books VALUES (NULL,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data["title"], data["author"], data["genre"],
        data["publish_year"], data["isbn"],
        data["available_copies"],
        datetime.date.today().isoformat()
    ))
    db.commit()
    return jsonify({"message": "Book added"}), 201

@app.route("/api/books/<int:id>", methods=["PUT"])
@token_required
def update_book(id):
    data = request.json
    cursor.execute("""
        UPDATE books SET title=%s, genre=%s, available_copies=%s WHERE book_id=%s
    """, (data["title"], data["genre"], data["available_copies"], id))
    db.commit()
    return jsonify({"message": "Book updated"})

@app.route("/api/books/<int:id>", methods=["DELETE"])
@token_required
def delete_book(id):
    cursor.execute("DELETE FROM books WHERE book_id=%s", (id,))
    db.commit()
    return jsonify({"message": "Book deleted"})

@app.route("/books/<int:id>")
def view_book(id):
    cursor.execute("SELECT * FROM books WHERE book_id = %s", (id,))
    book = cursor.fetchone()

    if not book:
        return "<h1>Book not found</h1>", 404

    html = f"""
    <h1>{book['title']}</h1>
    <p><strong>Book ID:</strong> {book['book_id']}</p>
    <p><strong>Genre:</strong> {book['genre']}</p>
    <p><strong>Publish Year:</strong> {book['publish_year']}</p>
    <p><strong>ISBN:</strong> {book['isbn']}</p>
    <p><strong>Available Copies:</strong> {book['available_copies']}</p>

    <br>
    <a href="/books">⬅ Back to Books</a>
    """

    return html

# ----------------------------------
# SEARCH
# ----------------------------------
@app.route("/api/search")
@token_required
def search():
    q = request.args.get("q", "")
    cursor.execute("SELECT * FROM books WHERE title LIKE %s OR genre LIKE %s",
                   (f"%{q}%", f"%{q}%"))
    return respond(cursor.fetchall())

# ----------------------------------
@app.route("/")
def index():
    return jsonify({"message": "Library API Running"})

@app.route("/authors")
def authors_page():
    cursor.execute("SELECT DISTINCT author FROM books WHERE author IS NOT NULL AND author != ''")
    authors = cursor.fetchall()

    html = """
    <h1>Authors</h1>
    <ul>
    {% for a in authors %}
        <li>{{ a.author }}</li>
    {% endfor %}
    </ul>
    <br>
    <a href="/books">⬅ Back to Books</a>
    """
    return render_template_string(html, authors=authors)


if __name__ == "__main__":
    seed_books()   
    app.run(debug=True)
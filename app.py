from flask import Flask, render_template, request, redirect, session, g, current_app
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

# Use a separate, explicit sqlite database filename to avoid conflicts with a non-SQLite file.
app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'database_sqlite.db')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

app.teardown_appcontext(close_db)

@app.route("/")
def index():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM sanpham")
    products = c.fetchall()
    return render_template("index.html", products=products)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (NULL, ?, ?)", (username, password))
        conn.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        if user:
            session["user"] = username
            session["cart"] = []
            return redirect("/")
    return render_template("login.html")

@app.route("/add/<int:id>")
def add_cart(id):
    session.setdefault("cart", [])
    session["cart"].append(id)
    return redirect("/cart")

@app.route("/cart")
def cart():
    conn = get_db()
    c = conn.cursor()
    items = []
    for pid in session.get("cart", []):
        c.execute("SELECT * FROM sanpham WHERE id=?", (pid,))
        items.append(c.fetchone())
    return render_template("cart.html", items=items)

@app.route("/admin")
def admin():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM sanpham")
    products = c.fetchall()
    return render_template("admin.html", products=products)

if __name__ == "__main__":
    app.run(debug=True)

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
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        address = request.form["address"]
        username = request.form["username"]
        password = request.form["password"]

        print(f"[REGISTER] Tạo tài khoản: username='{username}', fullname='{fullname}', email='{email}'")

        conn = get_db()
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (fullname, email, phone, address, username, password) VALUES (?, ?, ?, ?, ?, ?)",
                (fullname, email, phone, address, username, password),
            )
            conn.commit()
            return redirect("/login")
        except sqlite3.IntegrityError:
            # Username đã tồn tại -> hiện thông báo lỗi trên form
            error = "Tên đăng nhập đã được sử dụng, vui lòng chọn tên khác."
            print(f"[REGISTER] Lỗi: {error} username='{username}'")
            return render_template(
                "register.html",
                error=error,
                fullname=fullname,
                email=email,
                phone=phone,
                address=address,
                username=username,
            )
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
            print(f"[LOGIN] Đăng nhập thành công với username='{username}'")
            return redirect("/")
        else:
            print(f"[LOGIN] Đăng nhập thất bại với username='{username}'")
    return render_template("login.html")

@app.route("/add/<int:id>")
def add_cart(id):
    # Lấy giỏ hàng hiện tại từ session (nếu chưa có thì là list rỗng)
    cart = session.get("cart", [])
    cart.append(id)
    # GÁN LẠI vào session để Flask nhận biết có thay đổi
    session["cart"] = cart
    print(f"[CART] Thêm sản phẩm id={id} vào giỏ. Cart hiện tại: {session['cart']}")
    return redirect("/cart")

@app.route("/cart")
def cart():
    print(f"[CART] Xem giỏ hàng. Cart trong session: {session.get('cart')}")
    conn = get_db()
    c = conn.cursor()
    items = []
    for pid in session.get("cart", []):
        c.execute("SELECT * FROM sanpham WHERE id=?", (pid,))
        row = c.fetchone()
        # Nếu sản phẩm không tồn tại (fetchone() trả về None) thì bỏ qua,
        # tránh lỗi "None has no element 2" trong template.
        if row is not None:
            items.append(row)
    return render_template("cart.html", items=items)

@app.route("/admin")
def admin():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM sanpham")
    products = c.fetchall()
    return render_template("admin.html", products=products)

@app.route("/profile")
def profile():
    # Yêu cầu phải đăng nhập
    if "user" not in session:
        return redirect("/login")
    username = session["user"]
    return render_template("profile.html", username=username)

@app.route("/settings")
def settings():
    # Yêu cầu phải đăng nhập
    if "user" not in session:
        return redirect("/login")
    username = session["user"]
    return render_template("settings.html", username=username)

@app.route("/logout")
def logout():
    # Xóa thông tin đăng nhập và giỏ hàng rồi quay về trang chủ
    session.pop("user", None)
    session.pop("cart", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)

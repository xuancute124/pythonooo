from flask import Flask, render_template, request, redirect, session, g, current_app
import sqlite3
import os
from datetime import datetime

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
    # Lọc theo category nếu có tham số ?category=
    selected_category = request.args.get("category", type=int)

    # Lọc theo khoảng giá: nhận nhiều giá trị từ checkbox, ví dụ: price=100-200
    selected_price_ranges = request.args.getlist("price")

    where_clauses = []
    params = []

    if selected_category:
        where_clauses.append("category_id = ?")
        params.append(selected_category)

    # Ánh xạ mã khoảng giá -> (min, max)
    price_map = {
        "0-100": (0, 100000),
        "100-200": (100000, 200000),
        "200-400": (200000, 400000),
        "400+": (400000, None),
    }

    price_conditions = []
    for code in selected_price_ranges:
        if code not in price_map:
            continue
        min_price, max_price = price_map[code]
        if max_price is None:
            price_conditions.append("gia >= ?")
            params.append(min_price)
        else:
            price_conditions.append("gia BETWEEN ? AND ?")
            params.extend([min_price, max_price])

    if price_conditions:
        where_clauses.append("(" + " OR ".join(price_conditions) + ")")

    query = "SELECT * FROM sanpham"
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    c.execute(query, params)
    products = c.fetchall()

    # Lấy danh sách category để hiển thị bộ lọc
    c.execute("SELECT * FROM categories")
    categories = c.fetchall()

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        selected_category=selected_category,
        selected_price_ranges=selected_price_ranges,
    )

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


@app.route("/product/<int:product_id>", methods=["GET", "POST"])
def product_detail(product_id):
    conn = get_db()
    c = conn.cursor()

    # Lấy thông tin sản phẩm
    c.execute("SELECT * FROM sanpham WHERE id=?", (product_id,))
    product = c.fetchone()
    if product is None:
        return "Sản phẩm không tồn tại", 404

    # Lấy tên category (loại sản phẩm) nếu có
    category_name = None
    if product["category_id"]:
        c.execute("SELECT name FROM categories WHERE id=?", (product["category_id"],))
        row_cat = c.fetchone()
        if row_cat:
            category_name = row_cat["name"]

    error = None
    success = None

    if request.method == "POST" and request.form.get("action") == "buy":
        card_name = request.form.get("card_name", "").strip()
        card_number = request.form.get("card_number", "").strip()
        expiry_date = request.form.get("expiry_date", "").strip()
        ccv = request.form.get("ccv", "").strip()

        # Validate đơn giản: không cho phép field rỗng
        if not card_name or not card_number or not expiry_date or not ccv:
            error = "Vui lòng điền đầy đủ thông tin thẻ ngân hàng."
        else:
            # Xác định user_id nếu đã đăng nhập
            user_id = None
            if "user" in session:
                c.execute("SELECT id FROM users WHERE username=?", (session["user"],))
                user_row = c.fetchone()
                if user_row:
                    user_id = user_row["id"]

            type_pay = "banking"
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            c.execute(
                """
                INSERT INTO payment_methods (user_id, type_pay, card_name, card_number, expiry_date, ccv, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, type_pay, card_name, card_number, expiry_date, ccv, created_at),
            )
            conn.commit()
            success = "Thanh toán thành công! Cảm ơn bạn đã mua hàng."

    return render_template(
        "product_detail.html",
        product=product,
        category_name=category_name,
        error=error,
        success=success,
    )

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

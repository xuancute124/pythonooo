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
            # Mặc định role là 'user' cho tài khoản đăng ký mới
            c.execute(
                "INSERT INTO users (fullname, email, phone, address, username, password, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (fullname, email, phone, address, username, password, "user"),
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
            session["role"] = user["role"]
            session["cart"] = []
            print(f"[LOGIN] Đăng nhập thành công với username='{username}', role='{user['role']}'")
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

            # Lưu thông tin thanh toán
            c.execute(
                """
                INSERT INTO payment_methods (user_id, type_pay, card_name, card_number, expiry_date, ccv, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, type_pay, card_name, card_number, expiry_date, ccv, created_at),
            )

            # Nếu có user đăng nhập thì lưu lịch sử mua hàng cho user đó
            if user_id is not None:
                c.execute(
                    """
                    INSERT INTO purchases (user_id, product_id, quantity, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, product_id, 1, created_at),
                )

            conn.commit()
            success = "Thanh toán thành công! Đơn hàng của bạn đã được ghi nhận."

    return render_template(
        "product_detail.html",
        product=product,
        category_name=category_name,
        error=error,
        success=success,
    )

@app.route("/admin")
def admin():
    # Chỉ cho phép role admin
    if session.get("role") != "admin":
        return "URL không khả dụng - bạn không có quyền truy cập trang quản trị.", 403

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM sanpham")
    products = c.fetchall()

    # Lấy categories để hiện tên loại trong bảng nếu cần
    c.execute("SELECT * FROM categories")
    categories = {row["id"]: row["name"] for row in c.fetchall()}

    return render_template("admin.html", products=products, categories=categories)


@app.route("/admin/product/new", methods=["GET", "POST"])
def admin_product_new():
    if session.get("role") != "admin":
        return "URL không khả dụng - bạn không có quyền truy cập trang quản trị.", 403
    conn = get_db()
    c = conn.cursor()

    # Lấy danh mục cho dropdown
    c.execute("SELECT * FROM categories")
    categories = c.fetchall()

    error = None
    if request.method == "POST":
        name = request.form.get("ten", "").strip()
        price = request.form.get("gia", "").strip()
        quantity = request.form.get("quantity", "").strip()
        size = request.form.get("size", "").strip()
        color = request.form.get("color", "").strip()
        description = request.form.get("description", "").strip()
        category_id = request.form.get("category_id", type=int)
        product_type = request.form.get("product_type", "").strip()

        if not name or not price:
            error = "Vui lòng nhập ít nhất tên và giá sản phẩm."
        else:
            created_at = datetime.now().strftime("%Y-%m-%d")
            c.execute(
                """
                INSERT INTO sanpham (ten, gia, quantity, size, color, description, category_id, product_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    int(price),
                    int(quantity) if quantity else 0,
                    size,
                    color,
                    description,
                    category_id,
                    product_type,
                    created_at,
                ),
            )
            conn.commit()
            return redirect("/admin")

    return render_template(
        "admin_product_form.html",
        mode="create",
        error=error,
        categories=categories,
        product=None,
    )


@app.route("/admin/product/<int:product_id>/edit", methods=["GET", "POST"])
def admin_product_edit(product_id):
    if session.get("role") != "admin":
        return "URL không khả dụng - bạn không có quyền truy cập trang quản trị.", 403
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM sanpham WHERE id=?", (product_id,))
    product = c.fetchone()
    if product is None:
        return "Sản phẩm không tồn tại", 404

    c.execute("SELECT * FROM categories")
    categories = c.fetchall()

    error = None
    if request.method == "POST":
        name = request.form.get("ten", "").strip()
        price = request.form.get("gia", "").strip()
        quantity = request.form.get("quantity", "").strip()
        size = request.form.get("size", "").strip()
        color = request.form.get("color", "").strip()
        description = request.form.get("description", "").strip()
        category_id = request.form.get("category_id", type=int)
        product_type = request.form.get("product_type", "").strip()

        if not name or not price:
            error = "Vui lòng nhập ít nhất tên và giá sản phẩm."
        else:
            c.execute(
                """
                UPDATE sanpham
                SET ten = ?, gia = ?, quantity = ?, size = ?, color = ?, description = ?, category_id = ?, product_type = ?
                WHERE id = ?
                """,
                (
                    name,
                    int(price),
                    int(quantity) if quantity else 0,
                    size,
                    color,
                    description,
                    category_id,
                    product_type,
                    product_id,
                ),
            )
            conn.commit()
            return redirect("/admin")

    return render_template(
        "admin_product_form.html",
        mode="edit",
        error=error,
        categories=categories,
        product=product,
    )


@app.route("/admin/product/<int:product_id>/delete", methods=["POST"])
def admin_product_delete(product_id):
    if session.get("role") != "admin":
        return "URL không khả dụng - bạn không có quyền truy cập trang quản trị.", 403
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM sanpham WHERE id=?", (product_id,))
    conn.commit()
    return redirect("/admin")

@app.route("/profile")
def profile():
    # Yêu cầu phải đăng nhập
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (session["user"],))
    user = c.fetchone()
    if user is None:
        return redirect("/logout")

    # Lấy danh sách sản phẩm đã mua của user (nếu có)
    c.execute(
        """
        SELECT p.id, p.ten, p.gia, pu.created_at
        FROM purchases pu
        JOIN sanpham p ON pu.product_id = p.id
        WHERE pu.user_id = ?
        ORDER BY pu.created_at DESC
        """,
        (user["id"],),
    )
    purchased_items = c.fetchall()

    return render_template("profile.html", user=user, purchased_items=purchased_items)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    # Yêu cầu phải đăng nhập
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (session["user"],))
    user = c.fetchone()
    if user is None:
        return redirect("/logout")

    profile_success = None
    profile_error = None
    password_success = None
    password_error = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_profile":
            fullname = request.form.get("fullname", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            address = request.form.get("address", "").strip()

            if not fullname or not email or not phone or not address:
                profile_error = "Vui lòng điền đầy đủ thông tin cá nhân."
            else:
                c.execute(
                    """
                    UPDATE users
                    SET fullname = ?, email = ?, phone = ?, address = ?
                    WHERE id = ?
                    """,
                    (fullname, email, phone, address, user["id"]),
                )
                conn.commit()
                profile_success = "Cập nhật thông tin cá nhân thành công."
                # Cập nhật lại biến user để hiển thị dữ liệu mới
                c.execute("SELECT * FROM users WHERE id=?", (user["id"],))
                user = c.fetchone()

        elif action == "change_password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not current_password or not new_password or not confirm_password:
                password_error = "Vui lòng điền đầy đủ thông tin mật khẩu."
            elif current_password != user["password"]:
                password_error = "Mật khẩu hiện tại không chính xác."
            elif new_password != confirm_password:
                password_error = "Mật khẩu mới và xác nhận mật khẩu không trùng khớp."
            else:
                c.execute(
                    "UPDATE users SET password = ? WHERE id = ?",
                    (new_password, user["id"]),
                )
                conn.commit()
                password_success = "Đổi mật khẩu thành công."

    return render_template(
        "settings.html",
        user=user,
        profile_success=profile_success,
        profile_error=profile_error,
        password_success=password_success,
        password_error=password_error,
    )

@app.route("/logout")
def logout():
    # Xóa thông tin đăng nhập, quyền và giỏ hàng rồi quay về trang chủ
    session.pop("user", None)
    session.pop("role", None)
    session.pop("cart", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)

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
    # Phân trang
    page = request.args.get("page", type=int, default=1)
    if page < 1:
        page = 1
    per_page = 8
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

    base_query = "FROM sanpham"
    where_sql = ""
    if where_clauses:
        where_sql = " WHERE " + " AND ".join(where_clauses)

    # Đếm tổng số sản phẩm để tính số trang
    count_query = "SELECT COUNT(*) " + base_query + where_sql
    c.execute(count_query, params)
    total_products = c.fetchone()[0]

    total_pages = (total_products + per_page - 1) // per_page if total_products > 0 else 1
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page

    # Lấy danh sách sản phẩm theo trang
    data_query = "SELECT * " + base_query + where_sql + " LIMIT ? OFFSET ?"
    c.execute(data_query, params + [per_page, offset])
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
        page=page,
        total_pages=total_pages,
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

    # Kiểm tra xem user hiện tại đã có phương thức thanh toán banking chưa
    has_payment = False
    saved_card = None
    if "user" in session:
        c.execute(
            """
            SELECT * FROM payment_methods
            WHERE user_id = (SELECT id FROM users WHERE username = ?)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (session["user"],),
        )
        saved_card = c.fetchone()
        if saved_card is not None:
            has_payment = True

    # Đọc thông báo từ session (nếu có) rồi xóa để tránh lặp lại
    cart_success = session.pop("cart_success", None)
    cart_error = session.pop("cart_error", None)

    return render_template(
        "cart.html",
        items=items,
        has_payment=has_payment,
        saved_card=saved_card,
        cart_success=cart_success,
        cart_error=cart_error,
    )


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

    # Lấy thông tin thẻ ngân hàng đã lưu (nếu có) cho user hiện tại
    saved_card = None
    if "user" in session:
        c.execute(
            """
            SELECT * FROM payment_methods
            WHERE user_id = (SELECT id FROM users WHERE username = ?)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (session["user"],),
        )
        saved_card = c.fetchone()

    if request.method == "POST" and request.form.get("action") == "buy":
        card_name = request.form.get("card_name", "").strip()
        card_number = request.form.get("card_number", "").strip()
        expiry_date = request.form.get("expiry_date", "").strip()
        ccv = request.form.get("ccv", "").strip()

        # Validate đơn giản: không cho phép field rỗng
        if not card_name or not card_number or not expiry_date or not ccv:
            error = "Vui lòng điền đầy đủ thông tin thẻ ngân hàng."
        else:
            # Kiểm tra tồn kho trước khi thanh toán
            c.execute("SELECT quantity FROM sanpham WHERE id=?", (product_id,))
            row_qty = c.fetchone()
            if row_qty is None or row_qty["quantity"] <= 0:
                error = "Sản phẩm đã hết hàng, vui lòng chọn sản phẩm khác."
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

                    # Tạo đơn hàng và chi tiết đơn hàng (orders / order_items)
                    total_amount = product["gia"]
                    c.execute(
                        "INSERT INTO orders (user_id, total_amount, created_at) VALUES (?, ?, ?)",
                        (user_id, total_amount, created_at),
                    )
                    order_id = c.lastrowid
                    c.execute(
                        """
                        INSERT INTO order_items (order_id, product_id, quantity, price)
                        VALUES (?, ?, ?, ?)
                        """,
                        (order_id, product_id, 1, product["gia"]),
                    )

                # Trừ tồn kho 1 sản phẩm
                c.execute(
                    "UPDATE sanpham SET quantity = quantity - 1 WHERE id = ? AND quantity > 0",
                    (product_id,),
                )

                conn.commit()
                success = "Thanh toán thành công! Đơn hàng của bạn đã được ghi nhận."

    return render_template(
        "product_detail.html",
        product=product,
        category_name=category_name,
        error=error,
        success=success,
        saved_card=saved_card,
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

    return render_template("admin.html", products=products, categories=categories, active_tab="inventory")


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


@app.route("/admin/product/<int:product_id>/quantity", methods=["POST"])
def admin_product_update_quantity(product_id):
    if session.get("role") != "admin":
        return "URL không khả dụng - bạn không có quyền truy cập trang quản trị.", 403

    quantity = request.form.get("quantity", type=int)
    if quantity is None or quantity < 0:
        return redirect("/admin")

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE sanpham SET quantity = ? WHERE id = ?", (quantity, product_id))
    conn.commit()
    return redirect("/admin")


@app.route("/cart/checkout", methods=["POST"])
def cart_checkout():
    # Yêu cầu phải đăng nhập để thanh toán
    if "user" not in session:
        session["cart_error"] = "Vui lòng đăng nhập trước khi thanh toán."
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    # Lấy user_id
    c.execute("SELECT id FROM users WHERE username=?", (session["user"],))
    user_row = c.fetchone()
    if user_row is None:
        session["cart_error"] = "Không tìm thấy tài khoản người dùng."
        return redirect("/cart")
    user_id = user_row["id"]

    # Kiểm tra xem user đã có thẻ lưu chưa
    c.execute(
        """
        SELECT * FROM payment_methods
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id,),
    )
    saved_card = c.fetchone()

    # Nếu chưa có thẻ thì đọc thông tin từ form và lưu mới
    if saved_card is None:
        card_name = request.form.get("card_name", "").strip()
        card_number = request.form.get("card_number", "").strip()
        expiry_date = request.form.get("expiry_date", "").strip()
        ccv = request.form.get("ccv", "").strip()

        if not card_name or not card_number or not expiry_date or not ccv:
            session["cart_error"] = "Vui lòng điền đầy đủ thông tin thẻ ngân hàng."
            return redirect("/cart")

        type_pay = "banking"
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            """
            INSERT INTO payment_methods (user_id, type_pay, card_name, card_number, expiry_date, ccv, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, type_pay, card_name, card_number, expiry_date, ccv, created_at),
        )
    else:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cart_ids = session.get("cart", [])
    if not cart_ids:
        session["cart_error"] = "Giỏ hàng trống."
        return redirect("/cart")

    # Đầu tiên: kiểm tra tồn kho và tính tổng tiền
    total_amount = 0
    products_in_cart = []
    for pid in cart_ids:
        # Kiểm tra tồn kho từng sản phẩm
        c.execute("SELECT quantity FROM sanpham WHERE id=?", (pid,))
        row_qty = c.fetchone()
        if row_qty is None or row_qty["quantity"] <= 0:
            # Nếu một sản phẩm hết hàng, dừng lại và báo lỗi
            session["cart_error"] = "Một hoặc nhiều sản phẩm trong giỏ đã hết hàng. Vui lòng kiểm tra lại giỏ hàng."
            conn.rollback()
            return redirect("/cart")

        c.execute("SELECT gia FROM sanpham WHERE id=?", (pid,))
        row_price = c.fetchone()
        if row_price is None:
            continue
        total_amount += row_price["gia"]
        products_in_cart.append({"id": pid, "price": row_price["gia"]})

    # Tạo bản ghi orders cho toàn bộ giỏ
    c.execute(
        "INSERT INTO orders (user_id, total_amount, created_at) VALUES (?, ?, ?)",
        (user_id, total_amount, created_at),
    )
    order_id = c.lastrowid

    # Ghi lại lịch sử mua hàng + chi tiết đơn + trừ tồn kho
    for p in products_in_cart:
        pid = p["id"]
        c.execute(
            """
            INSERT INTO purchases (user_id, product_id, quantity, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, pid, 1, created_at),
        )
        c.execute(
            """
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
            """,
            (order_id, pid, 1, p["price"]),
        )
        c.execute(
            "UPDATE sanpham SET quantity = quantity - 1 WHERE id = ? AND quantity > 0",
            (pid,),
        )

    # Clear giỏ hàng
    session["cart"] = []
    conn.commit()
    session["cart_success"] = "Thanh toán thành công! Đơn hàng của bạn đã được ghi nhận."
    return redirect("/cart")

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

    return render_template("profile.html", user=user)


@app.route("/orders")
def orders():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (session["user"],))
    user = c.fetchone()
    if user is None:
        return redirect("/logout")

    c.execute(
        """
        SELECT id, total_amount, created_at, status
        FROM orders
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user["id"],),
    )
    orders = c.fetchall()

    return render_template("orders.html", orders=orders)


@app.route("/orders/<int:order_id>")
def order_detail(order_id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    # Nếu là admin: được xem mọi đơn
    if session.get("role") == "admin":
        c.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = c.fetchone()
        if order is None:
            return "Đơn hàng không tồn tại.", 404
    else:
        # User thường: chỉ xem được đơn của chính mình
        c.execute("SELECT id FROM users WHERE username=?", (session["user"],))
        user = c.fetchone()
        if user is None:
            return redirect("/logout")

        c.execute(
            """
            SELECT * FROM orders
            WHERE id = ? AND user_id = ?
            """,
            (order_id, user["id"]),
        )
        order = c.fetchone()
        if order is None:
            return "Đơn hàng không tồn tại hoặc bạn không có quyền truy cập.", 404

    # Lấy chi tiết sản phẩm trong đơn
    c.execute(
        """
        SELECT oi.product_id, oi.quantity, oi.price, p.ten
        FROM order_items oi
        JOIN sanpham p ON oi.product_id = p.id
        WHERE oi.order_id = ?
        """,
        (order_id,),
    )
    items = c.fetchall()

    return render_template("order_detail.html", order=order, items=items)


@app.route("/admin/orders/<int:order_id>")
def admin_order_detail(order_id):
    # Chỉ cho phép admin xem chi tiết mọi đơn hàng
    if session.get("role") != "admin":
        return "URL không khả dụng - bạn không có quyền truy cập trang quản trị.", 403

    conn = get_db()
    c = conn.cursor()

    # Lấy đơn hàng kèm username
    c.execute(
        """
        SELECT o.*, u.username
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.id = ?
        """,
        (order_id,),
    )
    order = c.fetchone()
    if order is None:
        return "Đơn hàng không tồn tại.", 404

    # Lấy chi tiết sản phẩm trong đơn
    c.execute(
        """
        SELECT oi.product_id, oi.quantity, oi.price, p.ten
        FROM order_items oi
        JOIN sanpham p ON oi.product_id = p.id
        WHERE oi.order_id = ?
        """,
        (order_id,),
    )
    items = c.fetchall()

    return render_template("order_detail.html", order=order, items=items)


@app.route("/admin/orders")
def admin_orders():
    if session.get("role") != "admin":
        return "URL không khả dụng - bạn không có quyền truy cập trang quản trị.", 403

    conn = get_db()
    c = conn.cursor()
    c.execute(
        """
        SELECT o.id, o.total_amount, o.created_at, o.status, u.username
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
        """
    )
    orders = c.fetchall()
    return render_template("admin_orders.html", orders=orders, active_tab="orders")


@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
def admin_order_update_status(order_id):
    if session.get("role") != "admin":
        return "URL không khả dụng - bạn không có quyền truy cập trang quản trị.", 403

    new_status = request.form.get("status", "").strip()
    if not new_status:
        return redirect("/admin/orders")

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    return redirect("/admin/orders")


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

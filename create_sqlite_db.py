import sqlite3

DB = 'database_sqlite.db'

def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Tạo lại bảng users với nhiều thông tin hơn và cột role
    c.execute('DROP TABLE IF EXISTS users')
    c.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user'   -- 'admin' hoặc 'user'
    )
    ''')

    # Tạo bảng categories
    c.execute('DROP TABLE IF EXISTS categories')
    c.execute('''
    CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    ''')

    # Dữ liệu mẫu cho categories
    category_samples = [
        ('Áo thun',),
        ('Quần jean',),
        ('Áo khoác',),
    ]
    c.executemany('INSERT INTO categories (name) VALUES (?)', category_samples)

    # Tạo lại bảng sanpham với nhiều thông tin hơn và cột category_id để lọc theo danh mục
    c.execute('DROP TABLE IF EXISTS sanpham')
    c.execute('''
    CREATE TABLE sanpham (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ten TEXT,              -- tên sản phẩm
        gia INTEGER,           -- giá
        quantity INTEGER,      -- số lượng tồn
        size TEXT,             -- các size, ví dụ: "M,L,XL,XXL"
        color TEXT,            -- màu sắc
        description TEXT,      -- mô tả sản phẩm
        category_id INTEGER,   -- loại sản phẩm (danh mục)
        product_type TEXT,     -- loại chi tiết hơn nếu cần (ví dụ: unisex, basic, slim-fit)
        created_at TEXT,       -- ngày tạo
        FOREIGN KEY (category_id) REFERENCES categories(id)
    )
    ''')

    # Dữ liệu mẫu cho sanpham (gán vào các category) - ít nhất 30 sản phẩm
    # ten, gia, quantity, size, color, description, category_id, product_type, created_at
    product_samples = [
        ('Áo thun nam basic', 150000, 50, 'M,L,XL,XXL', 'Trắng,Đen,Xanh navy',
         'Áo thun basic chất cotton thoáng mát, form regular fit.', 1, 'T-shirt / Basic', '2025-01-01'),
        ('Áo thun nữ oversize', 170000, 40, 'M,L,XL', 'Hồng,Trắng,Đen',
         'Áo thun oversize nữ, dễ phối với jean hoặc chân váy.', 1, 'T-shirt / Oversize', '2025-01-02'),
        ('Áo thun unisex logo nhỏ', 190000, 60, 'M,L,XL,XXL', 'Trắng,Đen,Xanh lá',
         'Áo thun unisex in logo nhỏ trước ngực, phù hợp nam nữ.', 1, 'T-shirt / Unisex', '2025-01-03'),
        ('Áo thun tay dài', 210000, 35, 'M,L,XL', 'Be,Đen,Xám',
         'Áo thun tay dài chất cotton co giãn, phù hợp thời tiết se lạnh.', 1, 'T-shirt / Long-sleeve', '2025-01-04'),
        ('Áo thun cổ polo', 230000, 30, 'M,L,XL', 'Trắng,Xanh navy,Đen',
         'Áo polo trẻ trung, thích hợp đi làm và đi chơi.', 1, 'Polo / Basic', '2025-01-05'),
        ('Áo thun thể thao', 250000, 45, 'M,L,XL', 'Xanh ngọc,Đen',
         'Áo thun thể thao thoát mồ hôi tốt, phù hợp tập gym.', 1, 'T-shirt / Sport', '2025-01-06'),
        ('Áo thun graphic streetwear', 260000, 40, 'M,L,XL', 'Trắng,Đen',
         'Áo thun in hình streetwear cá tính, chất liệu dày dặn.', 1, 'T-shirt / Graphic', '2025-01-07'),
        ('Áo thun croptop nữ', 180000, 35, 'S,M,L', 'Trắng,Đen,Hồng',
         'Áo croptop nữ, phối cùng quần jean hoặc chân váy.', 1, 'T-shirt / Crop', '2025-01-08'),
        ('Áo thun sọc ngang', 200000, 30, 'M,L,XL', 'Trắng-Đen,Xanh-Trắng',
         'Áo thun sọc ngang phong cách Hàn Quốc.', 1, 'T-shirt / Stripe', '2025-01-09'),
        ('Áo thun vintage', 220000, 25, 'M,L,XL', 'Nâu,Be,Xanh rêu',
         'Áo thun phong cách vintage, chất vải mềm.', 1, 'T-shirt / Vintage', '2025-01-10'),

        ('Quần jean nữ skinny', 350000, 30, 'S,M,L,XL', 'Xanh nhạt,Đen',
         'Quần jean skinny co giãn nhẹ, tôn dáng.', 2, 'Jeans / Skinny', '2025-01-11'),
        ('Quần jean nam slim-fit', 330000, 45, 'M,L,XL,XXL', 'Xanh đậm,Đen',
         'Quần jean nam slim-fit, ít nhăn, dễ phối.', 2, 'Jeans / Slim-fit', '2025-01-12'),
        ('Quần jean ống rộng nữ', 370000, 35, 'S,M,L', 'Xanh nhạt,Xanh đậm',
         'Quần jean ống rộng hot trend, che khuyết điểm chân.', 2, 'Jeans / Wide-leg', '2025-01-13'),
        ('Quần jean rách gối', 360000, 25, 'M,L,XL', 'Xanh bạc,Đen',
         'Quần jean rách gối phong cách cá tính.', 2, 'Jeans / Distressed', '2025-01-14'),
        ('Quần jean baggy unisex', 340000, 40, 'M,L,XL', 'Xanh,Đen',
         'Quần jean baggy rộng rãi, phong cách đường phố.', 2, 'Jeans / Baggy', '2025-01-15'),
        ('Quần jean trắng', 380000, 20, 'M,L,XL', 'Trắng',
         'Quần jean trắng dễ phối, phù hợp mùa hè.', 2, 'Jeans / White', '2025-01-16'),
        ('Quần jean cạp cao', 360000, 30, 'S,M,L', 'Xanh nhạt,Đen',
         'Quần jean cạp cao, giúp tôn dáng và che bụng.', 2, 'Jeans / High-waist', '2025-01-17'),
        ('Quần short jean nữ', 290000, 35, 'S,M,L', 'Xanh nhạt,Trắng',
         'Quần short jean năng động cho mùa hè.', 2, 'Jeans / Shorts', '2025-01-18'),
        ('Quần jean ống loe', 390000, 20, 'S,M,L', 'Xanh đậm,Đen',
         'Quần jean ống loe phong cách retro.', 2, 'Jeans / Flare', '2025-01-19'),
        ('Quần jean form Hàn', 350000, 30, 'M,L,XL', 'Xanh đá,Đen',
         'Quần jean form Hàn Quốc, dáng đứng.', 2, 'Jeans / Straight', '2025-01-20'),

        ('Áo khoác daily', 450000, 25, 'M,L,XL', 'Đen,Xám,Xanh rêu',
         'Áo khoác nhẹ, chống gió, phù hợp mặc hằng ngày.', 3, 'Jacket / Daily', '2025-01-21'),
        ('Áo khoác bomber', 520000, 20, 'M,L,XL', 'Đen,Xanh rêu,Nâu',
         'Áo khoác bomber cá tính, lót mỏng.', 3, 'Jacket / Bomber', '2025-01-22'),
        ('Áo khoác jeans', 550000, 18, 'M,L,XL', 'Xanh nhạt,Đen',
         'Áo khoác jean basic, dễ phối với mọi outfit.', 3, 'Jacket / Denim', '2025-01-23'),
        ('Áo khoác hoodie nỉ', 420000, 40, 'M,L,XL', 'Đen,Trắng,Xám',
         'Hoodie nỉ ấm, form rộng, phù hợp thời tiết se lạnh.', 3, 'Hoodie / Basic', '2025-01-24'),
        ('Áo khoác dù', 480000, 30, 'M,L,XL', 'Đen,Xanh navy,Đỏ',
         'Áo khoác dù chống nước nhẹ, phong cách thể thao.', 3, 'Jacket / Windbreaker', '2025-01-25'),
        ('Áo blazer basic', 520000, 22, 'M,L,XL', 'Đen,Be,Nâu',
         'Blazer basic, phù hợp đi làm, dự sự kiện.', 3, 'Blazer / Basic', '2025-01-26'),
        ('Áo khoác cardigan len', 400000, 28, 'M,L', 'Be,Nâu,Xanh rêu',
         'Cardigan len mỏng, phối cùng đầm hoặc áo thun.', 3, 'Cardigan / Knit', '2025-01-27'),
        ('Áo khoác dạ dài', 650000, 15, 'M,L', 'Be,Đen,Xám',
         'Áo khoác dạ dáng dài, sang trọng, ấm áp.', 3, 'Coat / Long', '2025-01-28'),
        ('Áo khoác phao ngắn', 600000, 18, 'M,L,XL', 'Đen,Xanh rêu',
         'Áo phao ngắn nhẹ, giữ ấm tốt.', 3, 'Jacket / Puffer', '2025-01-29'),
        ('Áo khoác len oversize', 430000, 25, 'M,L', 'Trắng,Be,Xanh pastel',
         'Áo khoác len oversize, phong cách Hàn.', 3, 'Cardigan / Oversize', '2025-01-30'),
    ]
    c.executemany(
        'INSERT INTO sanpham (ten, gia, quantity, size, color, description, category_id, product_type, created_at) '
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        product_samples
    )

    # Bảng lưu phương thức thanh toán (payment_methods)
    c.execute('DROP TABLE IF EXISTS payment_methods')
    c.execute('''
    CREATE TABLE payment_methods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,        -- có thể null nếu khách chưa đăng nhập
        type_pay TEXT,          -- ví dụ: "banking"
        card_name TEXT,         -- tên chủ thẻ
        card_number TEXT,       -- số thẻ (demo, thực tế không nên lưu plain text)
        expiry_date TEXT,       -- ngày hết hạn
        ccv TEXT,               -- mã bảo mật (demo)
        created_at TEXT,        -- ngày tạo giao dịch
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Bảng lưu lịch sử mua hàng (purchases) - log chi tiết từng sản phẩm
    c.execute('DROP TABLE IF EXISTS purchases')
    c.execute('''
    CREATE TABLE purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,       -- người mua (có thể null nếu mua không đăng nhập)
        product_id INTEGER,    -- sản phẩm đã mua
        quantity INTEGER,      -- số lượng (mặc định 1 với "Mua ngay")
        created_at TEXT,       -- thời gian mua
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES sanpham(id)
    )
    ''')

    # Bảng orders (đơn hàng)
    c.execute('DROP TABLE IF EXISTS order_items')
    c.execute('DROP TABLE IF EXISTS orders')
    c.execute('''
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,        -- người mua
        total_amount INTEGER,   -- tổng tiền đơn hàng
        created_at TEXT,        -- thời gian tạo
        status TEXT DEFAULT 'completed', -- trạng thái đơn
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Bảng order_items (chi tiết sản phẩm theo đơn)
    c.execute('''
    CREATE TABLE order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price INTEGER,          -- đơn giá tại thời điểm mua
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES sanpham(id)
    )
    ''')

    # Tạo một tài khoản admin mẫu (username: admin / password: admin)
    c.execute(
        "INSERT INTO users (fullname, email, phone, address, username, password, role) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Quản trị viên", "admin@example.com", "0123456789", "Hà Nội", "admin", "c", "admin"),
    )

    conn.commit()
    conn.close()
    print(f'Created {DB} with sample data.')

if __name__ == '__main__':
    main()


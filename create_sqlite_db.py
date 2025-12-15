import sqlite3

DB = 'database_sqlite.db'

def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Tạo lại bảng users với nhiều thông tin hơn
    c.execute('DROP TABLE IF EXISTS users')
    c.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        username TEXT UNIQUE,
        password TEXT
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

    # Dữ liệu mẫu cho sanpham (gán vào các category)
    product_samples = [
        # ten, gia, quantity, size, color, description, category_id, product_type, created_at
        (
            'Áo thun nam basic', 150000, 50,
            'M,L,XL,XXL',
            'Trắng,Đen,Xanh navy',
            'Áo thun basic chất cotton thoáng mát, form regular fit phù hợp đi học, đi chơi.',
            1,
            'T-shirt / Basic',
            '2025-01-01'
        ),
        (
            'Áo thun nữ oversize', 170000, 40,
            'M,L,XL',
            'Hồng,Trắng,Đen',
            'Áo thun oversize nữ, dễ phối với jean hoặc chân váy, chất vải dày dặn.',
            1,
            'T-shirt / Oversize',
            '2025-01-02'
        ),
        (
            'Quần jean nữ skinny', 350000, 30,
            'M,L,XL',
            'Xanh nhạt,Đen',
            'Quần jean skinny co giãn nhẹ, tôn dáng, phù hợp đi làm và đi chơi.',
            2,
            'Jeans / Skinny',
            '2025-01-03'
        ),
        (
            'Quần jean nam slim-fit', 330000, 45,
            'M,L,XL,XXL',
            'Xanh đậm,Đen',
            'Quần jean nam slim-fit, ít nhăn, dễ phối với áo sơ mi hoặc áo thun.',
            2,
            'Jeans / Slim-fit',
            '2025-01-04'
        ),
        (
            'Áo khoác daily', 450000, 25,
            'M,L,XL',
            'Đen,Xám,Xanh rêu',
            'Áo khoác nhẹ, chống gió, phù hợp mặc hằng ngày, dễ phối đồ.',
            3,
            'Jacket / Daily',
            '2025-01-05'
        ),
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

    conn.commit()
    conn.close()
    print(f'Created {DB} with sample data.')

if __name__ == '__main__':
    main()


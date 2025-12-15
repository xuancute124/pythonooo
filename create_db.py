import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# Bảng người dùng
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")

# Bảng sản phẩm
c.execute("""
CREATE TABLE IF NOT EXISTS sanpham (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT,
    gia INTEGER
)
""")

# Dữ liệu mẫu
c.execute("DELETE FROM sanpham")
c.execute("INSERT INTO sanpham (ten, gia) VALUES ('Áo thun nam', 150000)")
c.execute("INSERT INTO sanpham (ten, gia) VALUES ('Quần jean nữ', 350000)")
c.execute("INSERT INTO sanpham (ten, gia) VALUES ('Áo khoác', 450000)")

conn.commit()
conn.close()

print("Đã tạo database thành công!")

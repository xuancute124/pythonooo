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

    c.execute('''
    CREATE TABLE IF NOT EXISTS sanpham (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ten TEXT,
        gia INTEGER
    )
    ''')

    # Replace sample data in sanpham
    c.execute('DELETE FROM sanpham')
    sample = [
        ('Áo thun nam', 150000),
        ('Quần jean nữ', 350000),
        ('Áo khoác', 450000),
    ]
    c.executemany('INSERT INTO sanpham (ten, gia) VALUES (?, ?)', sample)

    conn.commit()
    conn.close()
    print(f'Created {DB} with sample data.')

if __name__ == '__main__':
    main()


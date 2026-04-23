import sqlite3

DB_PATH = "db/all_stocks.db"

def create_tables():
    conn = sqlite3.connect(DB_PATH)

    # stock_price
    conn.execute("""
    CREATE TABLE IF NOT EXISTS stock_price(
        ticker TEXT,
        date TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        PRIMARY KEY (ticker, date)
    )
    """)


    # stock_master
    conn.execute("""
    CREATE TABLE IF NOT EXISTS stock_master (
        ticker TEXT PRIMARY KEY,
        company_name TEXT,
        market TEXT
    )
    """)

    conn.commit()
    conn.close()

    print("テーブル作成完了")

if __name__ == "__main__":
    create_tables()
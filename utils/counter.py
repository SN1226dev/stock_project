import sqlite3
DB_PATH = "db/light.db"
def init_counter():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS app_counter (
        id INTEGER PRIMARY KEY,
        count INTEGER
    )
    """)
    conn.execute("""
    INSERT OR IGNORE INTO app_counter (id, count) VALUES (1, 0)
    """)
    conn.commit()
    conn.close()


def update_counter():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
    UPDATE app_counter SET count = count + 1 WHERE id = 1
    """)

    count = conn.execute("""
    SELECT count FROM app_counter WHERE id = 1
    """).fetchone()[0]

    conn.commit()
    conn.close()

    return count
# src/db_utils.py

import sqlite3
import pandas as pd

DB_PATH = "db/light.db"

def load_price_data():
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql("""
    SELECT ticker, date, volume, close
    FROM stock_price
    """, conn)

    conn.close()
    return df
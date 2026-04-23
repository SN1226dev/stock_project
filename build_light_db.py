import sqlite3
import pandas as pd

FULL_DB = "db/all_stocks.db"
LIGHT_DB = "db/light.db"
print("★★★ build_light_db 実行された ★★★")
def build_light_db():
    conn = sqlite3.connect(FULL_DB)

    print("データ抽出中（直近2年）...")

    df_price = pd.read_sql("""
    SELECT *
    FROM stock_price
    WHERE date >= date('now', '-2 years')
    """, conn)

    df_master = pd.read_sql("""
    SELECT *
    FROM stock_master
    """, conn)

    conn.close()

    print("light.db作成中...")

    conn_light = sqlite3.connect(LIGHT_DB)

    df_price.to_sql("stock_price", conn_light, if_exists="replace", index=False)
    df_master.to_sql("stock_master", conn_light, if_exists="replace", index=False)

    # インデックス（高速化）
    conn_light.execute("""
    CREATE INDEX IF NOT EXISTS idx_ticker_date
    ON stock_price(ticker, date)
    """)

    conn_light.commit()
    conn_light.close()

    print("light.db作成完了")

if __name__ == "__main__":
    build_light_db()
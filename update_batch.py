#update_batch.py

import sqlite3
import pandas as pd
import time
from db_utils import update_stock
from datetime import datetime
DB_PATH = "db/all_stocks.db"


# =====================
# メイン処理
# =====================
def main():

    conn = sqlite3.connect(DB_PATH)

    tickers_df = pd.read_sql("""
    SELECT ticker
    FROM stock_master
    WHERE market LIKE '%プライム%'
    or market LIKE '%グロース%'
    or market LIKE '%スタンダード%'
    """, conn)

    conn.close()

    tickers = tickers_df["ticker"].tolist()
    print(f"[INFO] 対象銘柄数: {len(tickers)}")

    target = tickers[:200]
    for i, ticker in enumerate(target, 1):
        try:
            print(f"[{i}/{len(tickers)}] {ticker}")
            update_stock(ticker)
            time.sleep(0.3)
        except Exception as e:
            print(f"{ticker} 失敗:", e)

    with open("log.txt", "a") as f:
        f.write(f"{datetime.now()} 完了（{len(target)}件処理）\n")
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("手動停止しました")

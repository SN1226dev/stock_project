#update_batch.py

import sqlite3
import pandas as pd
import time
from db_utils import update_stock
DB_PATH = "all_stocks.db"




# =====================
# メイン処理
# =====================
def main():

    conn = sqlite3.connect(DB_PATH)

    tickers_df = pd.read_sql("""
    SELECT コード
    FROM stock_master
    WHERE 市場・商品区分 LIKE '%プライム%'
    or 市場・商品区分 LIKE '%グロース%'
    or 市場・商品区分 LIKE '%スタンダード%'
    """, conn)

    conn.close()

    tickers = [f"{code}.T" for code in tickers_df["コード"].tolist()]
    print(f"[INFO] 対象銘柄数: {len(tickers)}")

    for i, ticker in enumerate(tickers[:15], 1):
        try:
            print(f"[{i}/{len(tickers)}] {ticker}")
            update_stock(ticker)
            time.sleep(0.3)
        except Exception as e:
            print(f"{ticker} 失敗:", e)

if __name__ == "__main__":
    main()

#db_utils.py.py
import sqlite3
import pandas as pd
import yfinance as yf
import time
DB_PATH = "all_stocks.db"

def update_stock(ticker):

    # DB接続
    conn = sqlite3.connect(DB_PATH)

    # 最新日付取得
    query = """
    SELECT MAX(date) as max_date
    FROM stock_price
    WHERE ticker = ?
    """
    last_date_df = pd.read_sql(query, conn, params=[ticker])
    last_date = last_date_df.loc[0, "max_date"]

    # 開始日決定
    if pd.isna(last_date):
        start_date = "2005-01-01"
    else:
        start_date = (
            pd.to_datetime(last_date) + pd.Timedelta(days=1)
        ).strftime("%Y-%m-%d")

    print(f"{ticker} | start: {start_date}")

    # データ取得
    df = yf.download(ticker, start=start_date, progress=False)

    if df.empty:
        print("追加データなし")
        conn.close()

        return

    # カラム整理
    df.columns = df.columns.get_level_values(0)
    df.columns.name = None

    df["ticker"] = ticker
    df = df.reset_index()

    # 🔥 日付フォーマット統一（超重要）
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

    # カラム名統一
    df = df.rename(columns={
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })

    df = df[["ticker", "date", "open", "high", "low", "close", "volume"]]


     # =====================
        # ⑤ 重複除去（最重要）
     # =====================
    existing_dates = pd.read_sql("""
    SELECT date FROM stock_price WHERE ticker = ?
    """, conn, params=[ticker])

    df = df[~df["date"].isin(existing_dates["date"])]

    if df.empty:
        print(f"{ticker}: 追加なし（重複）")
        conn.close()
        return

    print(f"{ticker}: {len(df)}件追加")


    # DBに追加
    df.to_sql(
        "stock_price",
        conn,
        if_exists="append",
        index=False
    )

    print("DB更新完了:", ticker)

    conn.commit()
    conn.close()

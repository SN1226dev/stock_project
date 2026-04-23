import sqlite3
import pandas as pd
import os

DB_PATH = "db/all_stocks.db"

def load_master():
    path = os.path.join("data", "data_j.xls")

    df = pd.read_excel(path)
    df = df[["コード", "銘柄名", "市場・商品区分"]]

    # 英語に変換
    df = df.rename(columns={
        "コード": "ticker",
        "銘柄名": "company_name",
        "市場・商品区分": "market"
    })

    # ticker整形
    df["ticker"] = df["ticker"].astype(str) + ".T"

    conn = sqlite3.connect(DB_PATH)

    df.to_sql("stock_master", conn, if_exists="append", index=False)

    conn.commit()
    conn.close()

    print("stock_master登録完了")

if __name__ == "__main__":
    load_master()
import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import requests 
from utils.counter import init_counter, update_counter

DB_PATH = "db/light.db"

st.title("株価データ取得ツールβ")
init_counter() 
try:
    if "counted" not in st.session_state:
        count = update_counter()
        st.session_state["count"] = count
        st.session_state["counted"] = True
    else:
        count = st.session_state["count"]

except:
    count = 0


@st.cache_data
def load_stock_data(ticker):
    conn = sqlite3.connect(DB_PATH)

    name_df = pd.read_sql("""
    SELECT company_name
    FROM stock_master
    WHERE ticker = ?
    """, conn, params=[ticker])

    company_name = name_df.iloc[0, 0] if not name_df.empty else None

    df = pd.read_sql("""
    SELECT *
    FROM stock_price
    WHERE ticker = ?
    ORDER BY date
    """, conn, params=[ticker])

    conn.close()

    df["company_name"] = company_name

    return df


conn = sqlite3.connect(DB_PATH)


tickers_df = pd.read_sql("""
SELECT t.ticker, m.company_name
FROM (
    SELECT DISTINCT ticker
    FROM stock_price
) t
LEFT JOIN stock_master m
ON t.ticker = m.ticker
ORDER BY t.ticker
""", conn)
conn.close()

# 表示用（会社名付き）
tickers_df["label"] = tickers_df["ticker"] + " (" + tickers_df["company_name"].fillna("") + ")"

selected_label = st.selectbox("銘柄選択", tickers_df["label"])

# ticker取り出し
ticker = tickers_df.loc[tickers_df["label"] == selected_label, "ticker"].values[0]
df = load_stock_data(ticker)


if df.empty:
    st.warning("データなし")
else:
    company_name = df["company_name"].iloc[0]
    st.success("データ取得完了")

    st.write("最終更新日:", df["date"].max())
    st.write("データ件数:", f"{len(df):,} 件")

    df["date"] = pd.to_datetime(df["date"])

    min_date = df["date"].min().date()
    max_date = df["date"].max().date()

    start_date, end_date = st.slider(
        "表示期間",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date)
    )

    df_view = df[
        (df["date"] >= pd.to_datetime(start_date)) &
        (df["date"] <= pd.to_datetime(end_date))
    ].copy()

    st.subheader("株価推移")

    fig, (ax1, ax2) = plt.subplots(
        2, 1,
        sharex=True,
        figsize=(10,6),
        gridspec_kw={'height_ratios': [3,1]}
    )

    ax1.plot(df_view["date"], df_view["close"], label="Close")

    df_view["ma25"] = df_view["close"].rolling(25).mean()
    ax1.plot(df_view["date"], df_view["ma25"], label="MA25")

    ax1.set_title("Price")
    ax1.legend()
    ax1.grid()

    ax2.bar(df_view["date"], df_view["volume"])
    ax2.set_title("Volume")

    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(fig)

    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="CSVダウンロード",
        data=csv,
        file_name=f"{ticker}.csv",
        mime="text/csv"
    )

st.divider()
st.caption(f"👀 累計訪問数：{count if count else 0}")
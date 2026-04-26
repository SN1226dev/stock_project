import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

from utils.counter import init_counter, update_counter
from src.db_utils import load_price_data
from src.ranking import create_volume_ranking

DB_PATH = "db/light.db"

st.title("📈 株価分析ダッシュボード")


# =========================
# アクセスカウンタ
# =========================
try:
    init_counter()

    if "counted" not in st.session_state:
        count = update_counter()
        st.session_state["count"] = count
        st.session_state["counted"] = True
    else:
        count = st.session_state["count"]
except Exception:
    count = 0


# =========================
# 個別銘柄データ取得
# =========================
@st.cache_data
def load_stock_data(ticker):
    conn = sqlite3.connect(DB_PATH)

    name_df = pd.read_sql("""
        SELECT company_name
        FROM stock_master
        WHERE ticker = ?
    """, conn, params=[ticker])

    company_name = name_df.iloc[0, 0] if not name_df.empty else ""

    df = pd.read_sql("""
        SELECT *
        FROM stock_price
        WHERE ticker = ?
        ORDER BY date
    """, conn, params=[ticker])

    conn.close()

    df["company_name"] = company_name
    return df


# =========================
# ランキング作成
# =========================
df_all = load_price_data()
ranking = create_volume_ranking(df_all)

conn = sqlite3.connect(DB_PATH)

master = pd.read_sql("""
    SELECT ticker, company_name
    FROM stock_master
""", conn)

conn.close()

ranking = ranking.merge(master, on="ticker", how="left")
ranking["company_name"] = ranking["company_name"].fillna("")


# =========================
# ランキング表示用テーブル
# =========================
ranking_view = ranking.copy()

ranking_view["順位"] = range(1, len(ranking_view) + 1)
ranking_view["銘柄"] = ranking_view["ticker"] + " " + ranking_view["company_name"]
ranking_view["前日比株価"] = (ranking_view["return_1d"] * 100).round(1).astype(str) + "%"
ranking_view["出来高倍率"] = ranking_view["vol_ratio"].round(1).astype(str) + "倍"
ranking_view["株価"] = ranking_view["close"].apply(lambda x: f"{int(x):,}円")
ranking_view["出来高"] = ranking_view["volume"].apply(lambda x: f"{int(x):,}株")
ranking_view["平均出来高"] = (
    ranking_view["volume"] / ranking_view["vol_ratio"]
).apply(lambda x: f"{int(x):,}株")

ranking_view = ranking_view[
      ["順位", "銘柄", "株価", "前日比株価", "出来高倍率", "出来高"]
]




top_n = st.slider("表示件数", 5, 50, 10)
st.subheader(f"🔥 出来高急増ランキング（TOP{top_n}）")

st.dataframe(
    ranking_view.head(top_n),
    use_container_width=True,
    height=400
)


# 👇 ここに追加（超重要）
options = ranking_view["銘柄"].head(top_n).tolist()

selected_label = st.selectbox(
    "銘柄選択",
    options,
    index=0  # ← これを追加
)
ticker = selected_label.split()[0]


# =========================
# 個別データ表示
# =========================
df_stock = load_stock_data(ticker)

if df_stock.empty:
    st.warning("データなし")

else:
    company_name = df_stock["company_name"].iloc[0]

    st.success(f"{ticker}（{company_name}） データ取得完了")

    st.write("最終更新日:", df_stock["date"].max())
    st.write("データ件数:", f"{len(df_stock):,} 件")

    df_stock["date"] = pd.to_datetime(df_stock["date"])

    min_date = df_stock["date"].min().date()
    max_date = df_stock["date"].max().date()

    start_date, end_date = st.slider(
        "表示期間",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date)
    )

    df_view = df_stock[
        (df_stock["date"] >= pd.to_datetime(start_date)) &
        (df_stock["date"] <= pd.to_datetime(end_date))
    ].copy()

    # =========================
    # グラフ
    # =========================
    st.subheader("📈 株価推移")

    fig, (ax1, ax2) = plt.subplots(
        2, 1,
        sharex=True,
        figsize=(10, 6),
        gridspec_kw={"height_ratios": [3, 1]}
    )

    ax1.plot(df_view["date"], df_view["close"], label="終値")

    df_view["ma25"] = df_view["close"].rolling(25).mean()
    ax1.plot(df_view["date"], df_view["ma25"], label="25日移動平均")

    ax1.set_title("株価")
    ax1.legend()
    ax1.grid()

    ax2.bar(df_view["date"], df_view["volume"])
    ax2.set_title("出来高")

    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(fig)

    # =========================
    # CSVダウンロード
    # =========================
    csv = df_view.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="📥 CSVダウンロード",
        data=csv,
        file_name=f"{ticker}.csv",
        mime="text/csv"
    )


# =========================
# フッター
# =========================
st.divider()

if count == 0:
    st.caption("👀 訪問数：計測中...")
else:
    st.caption(f"👀 累計訪問数：{count}")
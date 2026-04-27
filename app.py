import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

from utils.counter import init_counter, update_counter
from src.db_utils import load_price_data
from src.ranking import create_volume_ranking

DB_PATH = "db/light.db"

st.title(" 株価分析ダッシュボードβ")

# =========================
# カウンタ
# =========================
try:
    init_counter()
    if "counted" not in st.session_state:
        count = update_counter()
        st.session_state["count"] = count
        st.session_state["counted"] = True
    else:
        count = st.session_state["count"]
except:
    count = 0

# =========================
# データ取得（軽量化）
# =========================
@st.cache_data(ttl=300)
def get_ranking():
    df_all = load_price_data()

    # 👇 ここ追加（超重要）
    df_all["date"] = pd.to_datetime(df_all["date"])
    df_all = df_all[
        df_all["date"] >= df_all["date"].max() - pd.Timedelta(days=60)
    ]

    ranking = create_volume_ranking(df_all)
    ranking = ranking.sort_values("score", ascending=False).head(30)

    return ranking

# 👇 ここも変更
ranking = get_ranking()



conn = sqlite3.connect(DB_PATH)
master = pd.read_sql("SELECT ticker, company_name FROM stock_master", conn)
conn.close()

ranking = ranking.merge(master, on="ticker", how="left")
ranking["company_name"] = ranking["company_name"].fillna("")

# =========================
# 表用データ
# =========================
ranking_view = ranking.copy()

ranking_view["順位"] = range(1, len(ranking_view) + 1)

ranking_view["銘柄"] = ranking_view["ticker"] + " " + ranking_view["company_name"]

ranking_view["株価"] = ranking_view["close"].apply(lambda x: f"{int(x):,}円")

ranking_view["前日比"] = (ranking_view["return_1d"] * 100).round(1).astype(str) + "%"

ranking_view["5日前株価"] = ranking_view["close_5d"].apply(
    lambda x: f"{int(x):,}円" if pd.notna(x) else "-"
)

ranking_view["5日騰落率"] = ranking_view["return_5d"].apply(
    lambda x: f"{round(x*100,1)}%" if pd.notna(x) else "-"
)

ranking_view["出来高倍率"] = ranking_view["vol_ratio"].round(1).astype(str) + "倍"

ranking_view["出来高"] = ranking_view["volume"].apply(lambda x: f"{int(x):,}株")

ranking_view = ranking_view[
    ["順位", "銘柄", "株価", "5日前株価", "5日騰落率", "前日比", "出来高倍率", "出来高"]
]

st.subheader(" 出来高急増ランキング")

# =========================
#  クリック選択（ここが神UI）
# =========================
event = st.dataframe(
    ranking_view,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row"
)

# 初期値（1位）
if "selected_ticker" not in st.session_state:
    st.session_state["selected_ticker"] = ranking.iloc[0]["ticker"]

# クリックされたら更新
if event.selection.rows:
    selected_index = event.selection.rows[0]
    st.session_state["selected_ticker"] = ranking.iloc[selected_index]["ticker"]

ticker = st.session_state["selected_ticker"]

# =========================
# 個別データ取得
# =========================
@st.cache_data
def load_stock_data(ticker):
    conn = sqlite3.connect(DB_PATH)

    name_df = pd.read_sql(
        "SELECT company_name FROM stock_master WHERE ticker = ?",
        conn,
        params=[ticker]
    )

    company_name = name_df.iloc[0, 0] if not name_df.empty else ""

    df = pd.read_sql(
        "SELECT * FROM stock_price WHERE ticker = ? ORDER BY date",
        conn,
        params=[ticker]
    )

    conn.close()
    df["company_name"] = company_name
    return df

df_stock = load_stock_data(ticker)

# =========================
# 詳細表示
# =========================
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

    # CSV
    csv = df_view.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "📥 CSVダウンロード",
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
import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "MS Gothic"
plt.rcParams["axes.unicode_minus"] = False

from utils.counter import init_counter, update_counter
from src.db_utils import load_price_data
from src.ranking import create_volume_ranking

DB_PATH = "db/light.db"

st.set_page_config(layout="wide")
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
st.markdown(
    "<h2 style='font-size:28px; margin-bottom:5px;'>📈 株価分析ダッシュボードβ</h2>",
    unsafe_allow_html=True
)

st.caption("出来高急増 × トレンド分析ツール")

# =========================
# CSS
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.card {
    background: linear-gradient(145deg, #0f0f0f, #1a1a1a);
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #2a2a2a;
    text-align: center;
    height: 80px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin-bottom: 10px;
}

.big {
    font-size: 22px;
    font-weight: bold;
    line-height: 1.4;
}

.label {
    color: #aaa;
    font-size: 11px;
    margin-bottom: 4px;
}

.green { color: #00ff88; }
.red { color: #ff4b4b; }
.orange { color: #ffaa00; }
.gray { color: #bbb; }

.chart-box {
    background-color: #0f0f0f;
    padding: 14px;
    border-radius: 12px;
    border: 1px solid #2a2a2a;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)


def card(label, value, color=None):
    color_class = ""

    if color == "green":
        color_class = "green"
    elif color == "red":
        color_class = "red"
    elif color == "orange":
        color_class = "orange"
    elif color == "gray":
        color_class = "gray"

    return f"""
    <div class="card">
        <div class="label">{label}</div>
        <div class="big {color_class}">{value}</div>
    </div>
    """


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
except Exception:
    count = 0


# =========================
# ランキング用データ取得
# =========================
@st.cache_data(ttl=300)
def get_ranking():
    df_all = load_price_data()

    df_all["date"] = pd.to_datetime(df_all["date"])
    df_all = df_all[
        df_all["date"] >= df_all["date"].max() - pd.Timedelta(days=60)
    ]

    ranking = create_volume_ranking(df_all)
    ranking = ranking.sort_values("score", ascending=False).head(30)

    return ranking


ranking = get_ranking()

if ranking.empty:
    st.warning("ランキングデータがありません")
    st.stop()


# =========================
# マスタ結合
# =========================
conn = sqlite3.connect(DB_PATH)
master = pd.read_sql("SELECT ticker, company_name FROM stock_master", conn)
conn.close()

ranking = ranking.merge(master, on="ticker", how="left")
ranking["company_name"] = ranking["company_name"].fillna("")


# =========================
# ランキング用シグナル計算
# =========================
@st.cache_data(ttl=300)
def get_signal_data():
    df_all = load_price_data()
    df_all["date"] = pd.to_datetime(df_all["date"])
    df_all = df_all.sort_values(["ticker", "date"])

    df_all["ma25"] = df_all.groupby("ticker")["close"].transform(
        lambda x: x.rolling(25).mean()
    )

    df_all["high20"] = df_all.groupby("ticker")["close"].transform(
        lambda x: x.rolling(20).max()
    )

    df_all["trend"] = df_all["close"] > df_all["ma25"]
    df_all["breakout"] = df_all["close"] > df_all.groupby("ticker")["high20"].shift(1)

    latest_signal = df_all.groupby("ticker").tail(1)

    return latest_signal[["ticker", "trend", "breakout"]]


signal_df = get_signal_data()

ranking = ranking.merge(signal_df, on="ticker", how="left")
ranking["trend"] = ranking["trend"].fillna(False)
ranking["breakout"] = ranking["breakout"].fillna(False)


# =========================
# ランキング表示用データ
# =========================
ranking_view = ranking.copy()

ranking_view["順位"] = range(1, len(ranking_view) + 1)

ranking_view["銘柄"] = (
    ranking_view["ticker"]
    + " "
    + ranking_view["company_name"].astype(str).str.slice(0, 18)
)

ranking_view["株価"] = ranking_view["close"].apply(
    lambda x: f"{int(x):,}円" if pd.notna(x) else "-"
)

ranking_view["前日比"] = ranking_view["return_1d"].apply(
    lambda x: f"{x * 100:.1f}%" if pd.notna(x) else "-"
)

ranking_view["出来高"] = ranking_view["volume"].apply(lambda x: f"{int(x):,}")

ranking_view["出来高倍率"] = ranking_view["vol_ratio"].apply(
    lambda x: f"{x:.1f}倍" if pd.notna(x) else "-"
)

ranking_view["トレンド"] = ranking_view["trend"].apply(
    lambda x: "🟢上昇" if x else "🔴下降"
)

ranking_view["シグナル"] = ranking_view["breakout"].apply(
    lambda x: "🔥BO" if x else "-"
)

ranking_view = ranking_view[
    ["順位", "銘柄", "株価", "前日比","出来高","出来高倍率", "トレンド", "シグナル"]
]


# =========================
# ランキング表示
# =========================
with st.expander("🔥 出来高急増ランキング", expanded=True):
    st.caption("👉 銘柄行をクリックすると下に詳細が表示されます")
    event = st.dataframe(
        ranking_view,
        use_container_width=True,
        hide_index=True,
        height=330,
        column_config={
            "順位": st.column_config.NumberColumn(width="small"),
            "銘柄": st.column_config.TextColumn(width="medium"),
            "株価": st.column_config.TextColumn(width="small"),
            "前日比": st.column_config.TextColumn(width="small"),
            "出来高": st.column_config.TextColumn(width="small"),
            "出来高倍率": st.column_config.TextColumn(width="small"),
            "トレンド": st.column_config.TextColumn(width="small"),
            "シグナル": st.column_config.TextColumn(width="small"),
        },
        on_select="rerun",
        selection_mode="single-row"
    )


# =========================
# 選択銘柄
# =========================
if "selected_ticker" not in st.session_state:
    st.session_state["selected_ticker"] = ranking.iloc[0]["ticker"]

if event.selection.rows:
    selected_index = event.selection.rows[0]
    st.session_state["selected_ticker"] = ranking.iloc[selected_index]["ticker"]

ticker = st.session_state["selected_ticker"]


# =========================
# 個別データ取得
# =========================
@st.cache_data(ttl=300)
def load_stock_data(ticker):
    conn = sqlite3.connect(DB_PATH)

    name_df = pd.read_sql(
        "SELECT company_name FROM stock_master WHERE ticker = ?",
        conn,
        params=[ticker]
    )

    company_name = name_df.iloc[0, 0] if not name_df.empty else ""

    df = pd.read_sql(
        """
        SELECT *
        FROM stock_price
        WHERE ticker = ?
        ORDER BY date DESC
        LIMIT 500
        """,
        conn,
        params=[ticker]
    )

    conn.close()

    df["company_name"] = company_name

    return df


df = load_stock_data(ticker)

if df.empty:
    st.warning("データなし")
    st.stop()

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")


# =========================
# 指標計算
# =========================
company_name = df["company_name"].iloc[0]

latest = df.iloc[-1]

close = latest["close"]
volume = latest["volume"]

prev_close = df["close"].iloc[-2] if len(df) >= 2 else None
close_5d = df["close"].iloc[-6] if len(df) >= 6 else None

ret1 = ((close / prev_close) - 1) * 100 if prev_close else 0
ret5 = ((close / close_5d) - 1) * 100 if close_5d else 0

df["ma25"] = df["close"].rolling(25).mean()
ma25 = df["ma25"].iloc[-1]

df["high20"] = df["close"].rolling(20).max()
high20_prev = df["high20"].shift(1).iloc[-1]

vol_ma = df["volume"].rolling(20).mean().iloc[-1]
vol_ratio = volume / vol_ma if pd.notna(vol_ma) and vol_ma > 0 else 0

trend_up = pd.notna(ma25) and close > ma25
trend_text = "上昇トレンド" if trend_up else "下降トレンド"
trend_color = "green" if trend_up else "red"

breakout = pd.notna(high20_prev) and close > high20_prev
breakout_text = "🔥ブレイクアウト" if breakout else "-"
breakout_color = "orange" if breakout else "gray"

ret1_color = "green" if ret1 >= 0 else "red"
ret5_color = "green" if ret5 >= 0 else "red"


# =========================
# ダッシュボード
# =========================
st.divider()
st.subheader(f"📊 {ticker}（{company_name}）")

col1, col2, col3, col4 = st.columns(4, gap="small")

col1.markdown(
    card("株価", f"{close:,.0f}円", "gray"),
    unsafe_allow_html=True
)

col2.markdown(
    card("前日比", f"{ret1:.1f}%", ret1_color),
    unsafe_allow_html=True
)

col3.markdown(
    card("5日変動", f"{ret5:.1f}%", ret5_color),
    unsafe_allow_html=True
)

col4.markdown(
    card("出来高倍率", f"{vol_ratio:.1f}倍", "gray"),
    unsafe_allow_html=True
)

col5, col6, col7, col8 = st.columns(4, gap="small")

col5.markdown(
    card("出来高", f"{volume:,.0f}株", "gray"),
    unsafe_allow_html=True
)

col6.markdown(
    card("トレンド", trend_text, trend_color),
    unsafe_allow_html=True
)

col7.markdown(
    card("シグナル", breakout_text, breakout_color),
    unsafe_allow_html=True
)

col8.markdown(
    card(
        "判定",
        "監視候補" if trend_up and vol_ratio >= 2 else "通常",
        "orange" if trend_up and vol_ratio >= 2 else "gray"
    ),
    unsafe_allow_html=True
)


# =========================
# グラフ
# =========================
st.subheader("📈 株価推移")

if "chart_days" not in st.session_state:
    st.session_state["chart_days"] = 120


# 左寄せボタン
btn1, btn2, btn3, spacer = st.columns([1, 1, 1, 9])

def period_button(col, label, days):
    selected = st.session_state["chart_days"] == days

    with col:
        if st.button(
            label,
            type="primary" if selected else "secondary",
            use_container_width=True
        ):
            st.session_state["chart_days"] = days

period_button(btn1, "3ヶ月", 90)
period_button(btn2, "半年", 180)
period_button(btn3, "1年", 365)


df_plot = df.tail(st.session_state["chart_days"])

st.caption(f"表示期間：直近 {len(df_plot)} 営業日")

st.markdown('<div class="chart-box">', unsafe_allow_html=True)

fig, (ax1, ax2) = plt.subplots(
    2,
    1,
    sharex=True,
    figsize=(12, 6),
    gridspec_kw={"height_ratios": [3, 1]}
)

# 背景
fig.patch.set_facecolor("#0f0f0f")
ax1.set_facecolor("#0f0f0f")
ax2.set_facecolor("#0f0f0f")

# 線・棒
ax1.plot(df_plot["date"], df_plot["close"], label="Close Price", linewidth=2)
ax1.plot(df_plot["date"], df_plot["ma25"], label="25-day MA", linewidth=2)

ax2.bar(df_plot["date"], df_plot["volume"], label="Volume")

# タイトル
ax1.set_title("Stock Price Trend", fontsize=14, color="white", pad=12)
ax2.set_title("Volume", fontsize=13, color="white", pad=10)

# 軸ラベル・目盛りを白くする
ax1.tick_params(axis="x", colors="white")
ax1.tick_params(axis="y", colors="white")
ax2.tick_params(axis="x", colors="white")
ax2.tick_params(axis="y", colors="white")

# 軸線
for ax in [ax1, ax2]:
    for spine in ax.spines.values():
        spine.set_color("#666")

# グリッドを見えるようにする
ax1.grid(True, color="#555", linestyle="--", linewidth=0.6, alpha=0.65)
ax2.grid(True, color="#555", linestyle="--", linewidth=0.6, alpha=0.65)

# 凡例
legend = ax1.legend(
    facecolor="#111",
    edgecolor="#777",
    labelcolor="white",
    framealpha=0.95
)

for text in legend.get_texts():
    text.set_color("white")

plt.xticks(rotation=45)
plt.tight_layout()

st.pyplot(fig)

st.markdown('</div>', unsafe_allow_html=True)


# =========================
# CSV
# =========================
csv = df.to_csv(index=False).encode("utf-8-sig")

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
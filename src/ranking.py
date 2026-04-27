import numpy as np
import pandas as pd

def create_volume_ranking(df):
    """
    出来高急増ランキングを作成
    """

    df = df.copy()

    # =========================
    # 前処理
    # =========================
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["ticker", "date"])

    # =========================
    # 指標作成
    # =========================

    # 前日比
    df["return_1d"] = df.groupby("ticker")["close"].pct_change()

    # 5日騰落率
    df["return_5d"] = df.groupby("ticker")["close"].pct_change(5)

    # 5日前株価
    df["close_5d"] = df.groupby("ticker")["close"].shift(5)

    # 出来高平均（前日まで）
    df["vol_ma20"] = df.groupby("ticker")["volume"].transform(
        lambda x: x.shift(1).rolling(20).mean()
    )

    # 出来高倍率
    df["vol_ratio"] = df["volume"] / df["vol_ma20"]

    # =========================
    # クリーニング
    # =========================
    df = df.replace([np.inf, -np.inf], np.nan)

    # =========================
    # 最新データだけ取得
    # =========================
    latest_date = df["date"].max()
    latest_df = df[df["date"] == latest_date].copy()

    # =========================
    # フィルター（ここかなり重要）
    # =========================
    latest_df = latest_df[
        (latest_df["volume"] > 500000) &       # 最低出来高
        (latest_df["vol_ma20"].notna()) &      # 初期除外
        (latest_df["return_5d"].notna())       # 5日データあるもの
    ]

    # =========================
    # スコア（ここが心臓）
    # =========================
    latest_df["score"] = (
        latest_df["vol_ratio"] * 2 +     # 出来高（注目度）
        latest_df["return_1d"] * 50 +    # 短期
        latest_df["return_5d"] * 30      # 中期トレンド
    )

    # =========================
    # ソート
    # =========================
    latest_df = latest_df.sort_values("score", ascending=False)

    return latest_df
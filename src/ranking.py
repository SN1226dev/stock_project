import numpy as np
import pandas as pd

def create_volume_ranking(df):

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["ticker", "date"])

    # 指標
    df["return_1d"] = df.groupby("ticker")["close"].pct_change()
    df["return_5d"] = df.groupby("ticker")["close"].pct_change(5)

    df["vol_ma20"] = df.groupby("ticker")["volume"].transform(
        lambda x: x.shift(1).rolling(20).mean()
    )
    df["vol_ratio"] = df["volume"] / df["vol_ma20"]

    df["ma25"] = df.groupby("ticker")["close"].transform(
        lambda x: x.rolling(25).mean()
    )

    df["high20"] = df.groupby("ticker")["close"].transform(
        lambda x: x.rolling(20).max()
    )

    df["trend"] = df["close"] > df["ma25"]
    df["breakout"] = df["close"] > df.groupby("ticker")["high20"].shift(1)

    # 最新
    latest = df.groupby("ticker").tail(1).copy()

    # フィルター
    latest = latest[
        (latest["volume"] > 500000) &
        (latest["vol_ma20"].notna()) &
        (latest["return_5d"].notna())
    ]

    # スコア
    latest["score"] = (
        latest["vol_ratio"] * 2 +
        latest["return_1d"] * 50 +
        latest["return_5d"] * 30
    )

    return latest.sort_values("score", ascending=False).head(30)
# src/ranking.py

import pandas as pd
import numpy as np


def create_volume_ranking(df):
    """
    出来高急増ランキングを作成

    Parameters
    ----------
    df : DataFrame
        必須カラム: ['ticker', 'date', 'volume']
    top_n : int
        上位何件出すか

    Returns
    -------
    DataFrame
    """

    df = df.copy()

    # 日付型変換（念のため）
    df["date"] = pd.to_datetime(df["date"])

    # 並び替え（重要）
    df = df.sort_values(["ticker", "date"])
    df["return_1d"] = df.groupby("ticker")["close"].pct_change()

    # 過去20日平均（前日まで）
    df["vol_ma20"] = df.groupby("ticker")["volume"].transform(
        lambda x: x.shift(1).rolling(20).mean()
    )

    # 増加率
    df["vol_ratio"] = df["volume"] / df["vol_ma20"]


    # 無限・NaN除去
    df = df.replace([np.inf, -np.inf], np.nan)

    # 最新日だけ
    latest_date = df["date"].max()
    latest_df = df[df["date"] == latest_date].copy()

    # フィルター（重要）
    latest_df = latest_df[
        (latest_df["volume"] > 500000) &  # 最低出来高
        (latest_df["vol_ma20"].notna())   # 初期データ除外
    ]

    # スコア（少し強化版）
    latest_df["score"] = latest_df["vol_ratio"] * np.log(latest_df["volume"])

    # ソート
    ranking = latest_df.sort_values("score", ascending=False)

    return ranking
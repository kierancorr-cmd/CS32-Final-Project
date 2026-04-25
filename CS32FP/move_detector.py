import pandas as pd
import numpy as np

# this file figures out which days are "major moves" worth calling out on the chart
# the idea is to flag days where the stock moved way more than normal (not just any 1% day)

def find_major_moves(df, window=30, threshold_multiplier=2.0, min_pct=3.0):
    """
    finds big up/down days using a rolling volatility baseline

    instead of hardcoding "flag anything over 5%" we scale by how volatile
    the stock normally is - a 5% day for TSLA is boring, for JNJ it's huge

    params:
        window: how many days to look back for "normal" volatility
        threshold_multiplier: how many stddevs above normal counts as a big move
        min_pct: also require at least this % move regardless (filters noise on low-vol stocks)
    """

    if df is None or df.empty:
        return pd.DataFrame()

    # daily returns
    df = df.copy()
    df["return"] = df["Close"].pct_change() * 100  # as percent

    # rolling std of returns - this is our baseline volatility estimate
    df["rolling_std"] = df["return"].rolling(window=window).std()

    # a day counts as "major" if:
    # 1. the absolute move is bigger than threshold_multiplier * recent_volatility
    # 2. AND the move is at least min_pct% in absolute terms
    df["threshold"] = df["rolling_std"] * threshold_multiplier
    df["is_major"] = (df["return"].abs() > df["threshold"]) & (df["return"].abs() > min_pct)

    # drop the warmup period where we don't have rolling data yet
    major_moves = df[df["is_major"] == True].copy()

    # if there are somehow too many flagged days, just take the top 20 biggest moves
    # (this can happen with super volatile penny stocks)
    if len(major_moves) > 20:
        major_moves = major_moves.nlargest(20, "return")

    return major_moves[["Close", "return", "Volume"]]

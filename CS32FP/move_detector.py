import pandas as pd
import numpy as np


def find_major_moves(
    df,
    vol_window: int = 30,
    threshold_multiplier: float = 3.0,
    min_pct: float = 4.0,
    move_window: int = 5,
    max_markers: int = 20,
):
    """
    Finds significant multi-day price moves by comparing rolling N-day returns
    against normal N-day volatility.

    Key design choices:
    - We measure returns over `move_window` days (default 5) rather than single
      days, so a slow 5-day grind up/down gets flagged just like a single
      shock day.
    - Volatility baseline is the rolling std of those same N-day returns, so
      the threshold scales naturally with each stock's character (TSLA vs JNJ).
    - Overlapping windows that all look "major" are collapsed into one marker
      (the peak of the cluster) so we don't spam the chart.

    Args:
        df:                   OHLCV DataFrame with a DatetimeIndex and a "Close" column.
        vol_window:           Days of history used to estimate normal N-day volatility.
        threshold_multiplier: Std-devs above baseline required to flag a move.
        min_pct:              Hard floor — move must be at least this % regardless of vol.
        move_window:          The N-day return window (3–5 is a good range).
        max_markers:          Safety cap; keeps penny-stock noise from flooding the chart.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # 1. N-day cumulative return at each row
    #    pct_change(N) gives  (Close[t] / Close[t-N]) - 1
    df["return"] = df["Close"].pct_change(move_window) * 100

    # 2. Rolling volatility of those N-day returns
    #    This is our "normal" baseline — if the stock usually moves 8%
    #    over 5 days, a 9% move isn't as interesting.
    df["rolling_std"] = df["return"].rolling(window=vol_window).std()

    # 3. Flag rows that exceed BOTH criteria
    df["threshold"] = df["rolling_std"] * threshold_multiplier
    df["is_major"] = (
        (df["return"].abs() > df["threshold"]) &
        (df["return"].abs() > min_pct)
    )

    # Drop the warmup rows where rolling_std is NaN
    major_moves = df[df["is_major"]].copy()

    if major_moves.empty:
        return pd.DataFrame()

    # 4. Deduplicate overlapping windows
    #    Multiple consecutive rows can all "see" the same underlying event
    #    through their N-day look-back. Collapse each such cluster down to
    #    a single marker at the row with the biggest absolute move.
    major_moves = _deduplicate_clusters(major_moves, gap_days=move_window)

    # 5. Hard cap, for extremely volatile instruments
    if len(major_moves) > max_markers:
        major_moves = major_moves.nlargest(max_markers, key=lambda df: df["return"].abs())
        # nlargest doesn't accept a callable like that — do it manually:
        major_moves = major_moves.iloc[
            major_moves["return"].abs().argsort()[::-1][:max_markers]
        ]

    return major_moves[["Close", "return", "Volume"]]


# helpers
# ----------------------------------------------------------------

def _deduplicate_clusters(moves_df: pd.DataFrame, gap_days: int) -> pd.DataFrame:
    """
    Collapses clusters of overlapping flagged rows into a single representative row.

    Two flagged rows belong to the same cluster when they are within `gap_days`
    calendar days of each other (i.e. their look-back windows overlap).
    We keep the row with the largest absolute return from each cluster.
    """
    if moves_df.empty:
        return moves_df

    # Work through the sorted index, grouping rows that are close together.
    sorted_idx = moves_df.sort_index().index.tolist()
    clusters: list[list] = []
    current_cluster = [sorted_idx[0]]

    for date in sorted_idx[1:]:
        gap = (date - current_cluster[-1]).days
        if gap <= gap_days:
            current_cluster.append(date)
        else:
            clusters.append(current_cluster)
            current_cluster = [date]
    clusters.append(current_cluster)

    # Pick the peak row from each cluster
    best_rows = []
    for cluster in clusters:
        cluster_df = moves_df.loc[cluster]
        best_idx = cluster_df["return"].abs().idxmax()
        best_rows.append(best_idx)

    return moves_df.loc[best_rows]

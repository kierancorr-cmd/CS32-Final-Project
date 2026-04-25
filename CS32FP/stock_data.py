import yfinance as yf
import pandas as pd
from datetime import datetime

# wrapper around yfinance so the rest of the app doesn't have to care about the details
def get_stock_history(ticker, start_date, end_date):
    """pull historical OHLCV data for a ticker between two dates"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)

        if df.empty:
            return None

        # just keep what we need
        df = df[["Open", "High", "Low", "Close", "Volume"]]
        df.index = pd.to_datetime(df.index)

        # yfinance sometimes returns timezone-aware index, strip it
        if df.index.tzinfo is not None:
            df.index = df.index.tz_localize(None)

        return df

    except Exception as e:
        print(f"Error fetching history for {ticker}: {e}")
        return None


def get_stock_info(ticker):
    # grab current price & daily change for display on the homepage tiles
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # sometimes yfinance is annoying and doesn't return currentPrice
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0

        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose") or price
        change = ((price - prev_close) / prev_close * 100) if prev_close else 0

        return {
            "price": price,
            "change": round(change, 2),
            "name": info.get("shortName") or info.get("longName") or ticker,
            "sector": info.get("sector", ""),
            "market_cap": info.get("marketCap", 0)
        }

    except Exception as e:
        print(f"Error fetching info for {ticker}: {e}")
        # return something safe so the UI doesn't break
        return {"price": 0, "change": 0, "name": ticker, "sector": "", "market_cap": 0}

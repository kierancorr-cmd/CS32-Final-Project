import sqlite3
import os

# just storing recently viewed tickers - nothing fancy
DB_PATH = "recently_viewed.db"

def init_db():
    # create the table if it doesn't exist yet
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS recently_viewed (
            ticker TEXT,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_recently_viewed(ticker):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # don't add duplicates - delete old entry first then reinsert so it bubbles to top
    c.execute("DELETE FROM recently_viewed WHERE ticker = ?", (ticker,))
    c.execute("INSERT INTO recently_viewed (ticker) VALUES (?)", (ticker,))

    # keep at most 10 recent tickers, prune old ones
    c.execute("""
        DELETE FROM recently_viewed WHERE ticker NOT IN (
            SELECT ticker FROM recently_viewed ORDER BY viewed_at DESC LIMIT 10
        )
    """)

    conn.commit()
    conn.close()

def get_recently_viewed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # most recently viewed first
    c.execute("SELECT ticker FROM recently_viewed ORDER BY viewed_at DESC LIMIT 8")
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

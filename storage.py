import sqlite3
import pandas as pd

DB_NAME = "finviz_tracker.db"

def init_db():
    """Initialize SQLite database for daily tracking."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_history (
            scan_date TEXT,
            ticker TEXT,
            company TEXT,
            pe TEXT,
            price TEXT,
            PRIMARY KEY (scan_date, ticker)
        )
    """)
    conn.commit()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doji_watchlist (
            setup_date TEXT,
            ticker TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            PRIMARY KEY (setup_date, ticker)
        )
    """)
    conn.commit()
    conn.close()
    
def save_doji_setups(df_dojis, setup_date):
    """Save today's identified Doji stocks into SQLite."""
    if df_dojis.empty:
        return
    conn = sqlite3.connect(DB_NAME)
    df_to_save = df_dojis.copy()
    df_to_save['setup_date'] = setup_date
    df_to_save.to_sql('doji_watchlist', conn, if_exists='append', index=False)
    conn.close()

def get_yesterdays_dojis(today_date):
    """Fetch stocks that formed a Doji on the most recent trading session prior to today."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Find the latest setup date prior to today
    cursor.execute("""
        SELECT DISTINCT setup_date FROM doji_watchlist 
        WHERE setup_date < ? 
        ORDER BY setup_date DESC LIMIT 1
    """, (today_date,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return pd.DataFrame(), None
    
    prev_date = row[0]
    
    # Query all Dojis from that previous date
    query = "SELECT ticker, doji_high, doji_low, doji_volume FROM doji_watchlist WHERE setup_date = ?"
    df_dojis = pd.read_sql_query(query, conn, params=(prev_date,))
    conn.close()
    
    return df_dojis, prev_date

def save_to_db(df, scan_date):
    """Save scan data into SQLite, avoiding duplicates for the same day."""
    conn = sqlite3.connect(DB_NAME)
    df_to_save = df.copy()
    df_to_save['scan_date'] = scan_date
    df_to_save.to_sql('scan_history', conn, if_exists='append', index=False)
    conn.close()

def get_new_entries(today_date):
    """Find stocks appearing today that were not present in the previous scan."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT scan_date FROM scan_history 
        WHERE scan_date < ? 
        ORDER BY scan_date DESC LIMIT 1
    """, (today_date,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return pd.DataFrame(), None
    
    prev_date = row[0]
    query = """
        SELECT ticker, company, pe, price 
        FROM scan_history 
        WHERE scan_date = ? 
        AND ticker NOT IN (
            SELECT ticker FROM scan_history WHERE scan_date = ?
        )
    """
    new_stocks = pd.read_sql_query(query, conn, params=(today_date, prev_date))
    conn.close()
    return new_stocks, prev_date
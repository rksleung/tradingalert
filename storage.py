import sqlite3
import pandas as pd
import datetime

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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doji_breakouts (
            breakout_date TEXT,
            setup_date TEXT,
            ticker TEXT,
            doji_high REAL,
            breakout_close REAL,
            volume_ratio REAL,
            PRIMARY KEY (breakout_date, ticker)
        )
    """)
    conn.commit()
    conn.close()
    
def save_doji_setups(df_dojis, setup_date):
    """Save today's identified Doji stocks into SQLite, ignoring duplicates if they already exist."""
    if df_dojis.empty:
        return
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    df_to_save = df_dojis.copy()
    df_to_save['setup_date'] = setup_date
    
    # Insert row by row safely using INSERT OR IGNORE to prevent duplicate key crashes
    for _, row in df_to_save.iterrows():
        cursor.execute("""
            INSERT OR IGNORE INTO doji_watchlist (setup_date, ticker, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row.get('setup_date'),
            row.get('ticker'),
            row.get('open', 0.0),
            row.get('high', 0.0),
            row.get('low', 0.0),
            row.get('close', 0.0),
            row.get('volume', 0)
        ))
        
    conn.commit()
    conn.close()

def get_latest_doji_setups():
    """Fetches the most recent Doji watchlist records from prior sessions (excluding today)."""
    today_date = datetime.date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Find the latest setup date strictly BEFORE today
    cursor.execute("SELECT MAX(setup_date) FROM doji_watchlist WHERE setup_date < ?", (today_date,))
    row = cursor.fetchone()
    
    if not row or not row[0]:
        conn.close()
        print("No prior Doji setups found in the database.")
        return pd.DataFrame(), None
        
    latest_date = row[0]
    
    # Query all records for that previous session date
    query = "SELECT ticker, high, volume FROM doji_watchlist WHERE setup_date = ?"
    df_dojis = pd.read_sql_query(query, conn, params=(latest_date,))
    conn.close()
    
    return df_dojis, latest_date

def save_doji_breakouts(df_breakouts, breakout_date):
    """Save triggered breakouts into SQLite, ignoring duplicates if already recorded."""
    if df_breakouts.empty:
        return
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    df_to_save = df_breakouts.copy()
    if 'breakout_date' not in df_to_save.columns:
        df_to_save['breakout_date'] = breakout_date
        
    for _, row in df_to_save.iterrows():
        cursor.execute("""
            INSERT OR IGNORE INTO doji_breakouts (breakout_date, setup_date, ticker, doji_high, breakout_close, volume_ratio)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            row.get('breakout_date'),
            row.get('setup_date'),
            row.get('ticker'),
            row.get('doji_high', 0.0),
            row.get('breakout_close', 0.0),
            row.get('volume_ratio', 0.0)
        ))
        
    conn.commit()
    conn.close()

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
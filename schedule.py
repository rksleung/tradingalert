import sys
import datetime
from storage import init_db, save_doji_setups, get_latest_doji_setups, save_doji_breakouts
from scanner import parse_filters_from_url, run_finviz_scan
from evaluation import evaluate_doji_breakouts
import yfinance as yf
import pandas as pd

def fetch_todays_ohlcv(df_finviz):
    """Takes the Finviz ticker list and fetches today's OHLCV data using yfinance."""
    if df_finviz.empty or 'ticker' not in df_finviz.columns:
        return pd.DataFrame()

    tickers = df_finviz['company'].tolist()
    print(f"Fetching today's OHLCV data for {len(tickers)} filtered tickers...")

    # Download the last 2 days of data for the exact tickers returned by Finviz
    data = yf.download(tickers, period="2d", group_by="ticker", threads=True, progress=False)

    records = []
    for ticker in tickers:
        try:
            hist = data if len(tickers) == 1 else data[ticker]
            hist = hist.dropna()
            
            if hist.empty:
                continue

            # Get today's candle (the last row)
            today_candle = hist.iloc[-1]
            
            records.append({
                'ticker': ticker,
                'open': float(today_candle['Open']),
                'high': float(today_candle['High']),
                'low': float(today_candle['Low']),
                'close': float(today_candle['Close']),
                'volume': int(today_candle['Volume'])
            })
        except Exception as e:
            print(f"Could not fetch OHLCV for {ticker}: {e}")
            continue

    return pd.DataFrame(records)

def run_daily_job(finviz_url):
    """Main execution function for the daily background scan and save."""
    print(f"\n[{datetime.datetime.now()}] Starting daily Finviz scan job...")
    
    # 1. Ensure database table exists
    init_db()
    
    # 2. Parse URL and run Finviz scan
    filters_list = parse_filters_from_url(finviz_url)
    print(f"Extracted filters: {filters_list}")
    
    df_finviz = run_finviz_scan(filters_list)
    print(df_finviz)
    
    if df_finviz.empty:
        print("No stocks returned from Finviz scan. Exiting job.")
        return
        
    print(f"Finviz returned {len(df_finviz)} stocks.")
    
    # 3. Fetch exact Open, High, Low, Close, Volume for those specific tickers
    df_ohlcv = fetch_todays_ohlcv(df_finviz)

    if df_ohlcv.empty:
        print("Failed to retrieve OHLCV data for the tickers. Exiting.")
        return

    # 4. Save results to SQLite using your doji watchlist schema
    today_date = datetime.date.today().strftime("%Y-%m-%d")
    save_doji_setups(df_ohlcv, today_date)

    print(f"SUCCESS: Saved {len(df_finviz)} stock records for {today_date} into SQLite.")
    print(df_finviz.head())

    # 5. Evaluate yesterday doji
    df_dojis, latest_date = get_latest_doji_setups()
    df_breakouts = evaluate_doji_breakouts(df_dojis, latest_date)
    save_doji_breakouts(df_breakouts, today_date)

    print(f"SUCCESS: Saved {len(df_breakouts)} stock records for {today_date} into SQLite.")
    print(df_breakouts.head())

if __name__ == "__main__":
    # Allow passing the Finviz URL as a command-line argument, or use a default fallback
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        # Default predefined URL if none is passed
        target_url = "https://finviz.com/screener?v=111&f=ind_stocksonlyspac,sh_float_o10,ta_candlestick_d,ta_highlow50d_a0to5h,ta_highlow52w_a0to10h"
        print("No URL argument provided. Using default fallback URL.")
        
    run_daily_job(target_url)
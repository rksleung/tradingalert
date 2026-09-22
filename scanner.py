import pandas as pd
from urllib.parse import urlparse, parse_qs
from finviz.screener import Screener

def parse_filters_from_url(finviz_url):
    """Extracts the filter array list from a given Finviz URL."""
    parsed_url = urlparse(finviz_url)
    query_params = parse_qs(parsed_url.query)
    filters_string = query_params.get("f", [""])[0]
    filters_list = [f.strip() for f in filters_string.split(",") if f.strip()]
    return filters_list

def run_finviz_scan(filters_list):
    """Runs the Finviz screener and returns a clean pandas DataFrame using the library's built-in method."""
    try:
        # Initialize the screener with the filter list
        stock_list = Screener(filters=filters_list, rows=20)
        
        if not stock_list:
            return pd.DataFrame()
            
        # Use the built-in finviz method to convert directly to a DataFrame
        # stock_list.to_csv("stocks.csv")
        df = stock_list.to_dataframe()
        print('done to dataframe')
        if df.empty:
            return pd.DataFrame()
            
        # Normalize column names for database compatibility (lowercase, remove special chars/spaces)
        df.columns = [c.lower().replace('%', 'pct').replace('/', '').strip() for c in df.columns]
        print('done df')
        return df
        
    except Exception as e:
        print(f"Error during Finviz scan: {e}")
        return pd.DataFrame()
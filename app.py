import streamlit as st
import datetime
from storage import init_db, save_to_db, get_new_entries
from scanner import parse_filters_from_url, run_finviz_scan

# Page config
st.set_page_config(page_title="Finviz Daily Tracker", layout="wide")

# Initialize database on load
init_db()

st.title("📈 Finviz URL-Driven Daily Scanner")
st.markdown("Paste your Finviz screener URL below to extract filters, run the scan, save to SQLite, and track new entries.")

finviz_url = st.text_input(
    "Paste Finviz Screener URL:", 
    placeholder="https://finviz.com/screener.ashx?v=111&f=idx_sp500,sec_technology,fa_pe_u20,sh_instown_o60"
)

if finviz_url:
    try:
        # Extract filters using scanner module
        filters_list = parse_filters_from_url(finviz_url)
        
        st.success("Successfully extracted filters from URL!")
        st.code(filters_list, language="python")
        
        if st.button("Run Scan & Update Tracker", type="primary"):
            today = datetime.date.today().strftime("%Y-%m-%d")
            
            with st.spinner("Scanning the market via Finviz..."):
                # Run scan using scanner module
                df_clean = run_finviz_scan(filters_list)
                
                if df_clean.empty:
                    st.warning("No stocks found matching these criteria.")
                else:
                    # Save results using database module
                    # save_to_db(df_clean, today)
                    
                    st.subheader(f"📊 Today's Scan Results ({today})")
                    st.metric(label="Total Matching Stocks", value=len(df_clean))
                    st.dataframe(df_clean, use_container_width=True)
                    
                    # Check for New Entries using database module
                    st.markdown("---")
                    st.subheader("🔥 Newly Highlighted Stocks")
                    new_stocks, prev_date = get_new_entries(today)
                    
                    if prev_date:
                        st.caption(f"Compared against previous scan on: {prev_date}")
                        if not new_stocks.empty:
                            st.success(f"Found {len(new_stocks)} new stocks entering the criteria today!")
                            st.dataframe(new_stocks, use_container_width=True)
                        else:
                            st.info("No new stocks compared to the previous scan.")
                    else:
                        st.info("This is your first recorded scan. Future runs will track daily changes here.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
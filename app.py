import streamlit as st
from collections import defaultdict
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Stream Chat Highlight Analyzer", page_icon="🔥", layout="wide")

# Sidebar settings for user control
st.sidebar.header("⚙️ Analyzer Settings")
top_n = st.sidebar.slider("Number of highlights to display", min_value=5, max_value=50, value=25)
time_window = st.sidebar.slider("Deduplication window (minutes)", min_value=1, max_value=5, value=2)

st.title("🔥 Stream Chat Highlight Analyzer")
st.markdown("Upload your Twitch chat log text file to instantly extract unique VOD peak timestamps and engagement volumes.")

uploaded_file = st.file_uploader("Upload chat log (.txt)", type=["txt"])

if uploaded_file is not None:
    content = uploaded_file.getvalue().decode("utf-8", errors="ignore").splitlines()
    
    minute_counts = defaultdict(int)
    valid_lines = 0

    for line in content:
        line = line.strip()
        if not line:
            continue
        try:
            if line.startswith("["):
                end_bracket = line.find("]")
                if end_bracket != -1:
                    time_str = line[1:end_bracket]
                    parts = time_str.split(":")
                    
                    total_seconds = 0
                    if len(parts) == 3:
                        h, m, s = map(int, parts)
                        total_seconds = h * 3600 + m * 60 + s
                    elif len(parts) == 2:
                        m, s = map(int, parts)
                        total_seconds = m * 60 + s
                    else:
                        continue
                        
                    minute_mark = total_seconds // 60
                    minute_counts[minute_mark] += 1
                    valid_lines += 1
        except Exception:
            continue

    if minute_counts:
        # Display top-level metric cards for professional feel
        col1, col2 = st.columns(2)
        col1.metric("Total Messages Scanned", f"{valid_lines:,}")
        
        sorted_peaks = sorted(minute_counts.items(), key=lambda x: x[1], reverse=True)
        
        shown_blocks = set()
        table_data = []
        report_text = f"🔥 TOP {top_n} UNIQUE VOD PEAK TIMESTAMPS:\n\n"

        for minute_mark, count in sorted_peaks:
            if any(abs(minute_mark - existing) <= time_window for existing in shown_blocks):
                continue
                
            hrs = minute_mark // 60
            mins = minute_mark % 60
            
            timestamp_str = f"{hrs:02d}:{mins:02d}:00"
            table_data.append({"Rank": len(table_data) + 1, "VOD Timestamp": timestamp_str, "Message Volume": count})
            report_text += f"- VOD Time: {timestamp_str} — {count} messages\n"
            
            shown_blocks.add(minute_mark)
            if len(table_data) >= top_n:
                break

        col2.metric("Highlights Extracted", f"{len(table_data)}")
        
        st.divider()
        st.subheader("📊 Top VOD Peak Timestamps")
        
        # Present data inside an interactive, clean data table
        df_peaks = pd.DataFrame(table_data)
        st.dataframe(df_peaks, use_container_width=True, hide_index=True)

        # Download Report Button
        st.download_button(
            label="📥 Download Highlight Report (.txt)",
            data=report_text,
            file_name="highlight_report.txt",
            mime="text/plain"
        )
    else:
        st.warning("Could not find valid timestamps. Check your chat text file format.")

import streamlit as st
from collections import defaultdict
import pandas as pd

st.title("🔥 Stream Chat Highlight Analyzer")
st.write("Upload your Twitch chat log text file to instantly get the top unique VOD peak timestamps.")

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
        st.success(f"Successfully processed {valid_lines:,} chat messages!")
        
        sorted_peaks = sorted(minute_counts.items(), key=lambda x: x[1], reverse=True)
        
        shown_blocks = set()
        table_data = []
        report_text = "🔥 TOP 25 UNIQUE VOD PEAK TIMESTAMPS:\n\n"

        for minute_mark, count in sorted_peaks:
            if any(abs(minute_mark - existing) <= 2 for existing in shown_blocks):
                continue
                
            hrs = minute_mark // 60
            mins = minute_mark % 60
            
            timestamp_str = f"{hrs:02d}:{mins:02d}:00"
            table_data.append({"VOD Timestamp": timestamp_str, "Message Volume": count})
            report_text += f"- VOD Time: {timestamp_str} — {count} messages\n"
            
            shown_blocks.add(minute_mark)
            if len(table_data) >= 25:
                break

        # Display Top Metrics
        col1, col2 = st.columns(2)
        col1.metric("Total Messages Scanned", f"{valid_lines:,}")
        col2.metric("Highlights Extracted", f"{len(table_data)}")

        st.subheader("Top Unique VOD Peak Timestamps:")
        
        # Display as a clean, professional dataframe table
        df_peaks = pd.DataFrame(table_data)
        st.dataframe(df_peaks, use_container_width=True)

        # Download Button
        st.download_button(
            label="📥 Download Report (.txt)",
            data=report_text,
            file_name="highlight_report.txt",
            mime="text/plain"
        )
    else:
        st.warning("Could not find valid timestamps. Check your chat text file format.")our chat text file format.")

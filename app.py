import streamlit as st
from collections import defaultdict
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Stream Chat Highlight Analyzer", page_icon="🔥", layout="wide")

# Custom CSS injection for modern dark-mode card styling & visual polish
st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 800;
            color: #ff4b4b;
            margin-bottom: 0px;
        }
        .sub-header {
            color: #a3a3a3;
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #1e1e24;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #333;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar settings for user control
st.sidebar.header("⚙️ Analyzer Settings")
top_n = st.sidebar.slider("Number of highlights to display", min_value=5, max_value=50, value=25)
time_window = st.sidebar.slider("Deduplication window (minutes)", min_value=1, max_value=5, value=2)

st.markdown('<p class="main-header">🔥 Stream Chat Highlight Analyzer</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Extract unique VOD peak timestamps and engagement volumes instantly.</p>', unsafe_allow_html=True)

# Option Selection for Input
input_method = st.radio("Choose Input Method:", ["Upload Chat Log (.txt)", "Paste Twitch VOD Link Helper"], horizontal=True)

content = None

if input_method == "Upload Chat Log (.txt)":
    st.info("💡 **Tip:** To get your chat log from a Twitch VOD, download and use **TwitchDownloader** to export the chat into a `.txt` file, then upload it below.")
    
    uploaded_file = st.file_uploader("Upload chat log (.txt)", type=["txt"])
    if uploaded_file is not None:
        content = uploaded_file.getvalue().decode("utf-8", errors="ignore").splitlines()

else:
    st.markdown("### 🔗 VOD Link & Chat Download Helper")
    st.write("Since Twitch blocks cloud servers from downloading chats automatically, use this quick workflow to grab your chat log file:")
    
    vod_url = st.text_input("Paste Twitch VOD URL (e.g., https://www.twitch.tv/videos/...)")
    
    if vod_url:
        st.info("Because Twitch requires local browser authorization to download chat logs directly, use **TwitchDownloader** to save your `.txt` chat log, then drop it right below!")
        
        st.markdown("---")
        fallback_file = st.file_uploader("Drop your downloaded VOD chat log here (.txt)", type=["txt"], key="link_fallback")
        if fallback_file is not None:
            content = fallback_file.getvalue().decode("utf-8", errors="ignore").splitlines()

if content is not None and len(content) > 0:
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
        st.divider()
        
        # Professional Metric Display Columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(label="💬 Total Messages Scanned", value=f"{valid_lines:,}")
        
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

        with col2:
            st.metric(label="⚡ Highlights Extracted", value=f"{len(table_data)}")
        
        st.markdown("### 📊 Top VOD Peak Timestamps")
        
        # Present data inside an interactive, clean data table
        df_peaks = pd.DataFrame(table_data)
        st.dataframe(df_peaks, use_container_width=True, hide_index=True)

        # Success celebration effect
        st.balloons()

        # Download Report Button
        st.download_button(
            label="📥 Download Highlight Report (.txt)",
            data=report_text,
            file_name="highlight_report.txt",
            mime="text/plain"
        )
    else:
        st.warning("Could not find valid timestamps. Check your chat text file format.")

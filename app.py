import streamlit as st
from collections import defaultdict
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Stream Chat Highlight Analyzer", 
    page_icon="🔥", 
    layout="wide"
)

# Custom CSS injection for modern dark-mode card styling & visual polish
st.markdown("""
    <style>
        .main-header {
            font-size: 2.8rem;
            font-weight: 900;
            color: #ff4b4b;
            margin-bottom: 0px;
            letter-spacing: -0.5px;
        }
        .sub-header {
            color: #9ca3af;
            font-size: 1.15rem;
            margin-bottom: 2rem;
        }
        .card-container {
            background-color: #18181b;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #27272a;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .stButton button {
            width: 100%;
            border-radius: 8px;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar settings for user control
st.sidebar.header("⚙️ Analyzer Parameters")
top_n = st.sidebar.slider("Number of highlights to display", min_value=5, max_value=50, value=25)
time_window = st.sidebar.slider("Deduplication window (minutes)", min_value=1, max_value=5, value=2)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Quick Guide")
st.sidebar.markdown("1. Export chat from your VOD using [TwitchDownloader](https://github.com/Lay295/TwitchDownloader).\n2. Upload the `.txt` log file.\n3. Instantly review peak engagement timestamps.")

# App Header Section (Visual Banner Integration)
st.image("https://static-cdn.jtvnw.net/cf_vods/d2nvs31859zcd8/75d9e5dbd7c541315bfa_kaicenat_41776994983_1729388485//thumb/thumb0-640x360.jpg", use_column_width=True)
st.divider()

st.markdown('<p class="main-header">🔥 Stream Chat Highlight Analyzer</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Automated volume-spike detection for finding elite VOD timestamps and chat peaks instantly.</p>', unsafe_allow_html=True)

# Input Section inside a clean container
st.markdown("### 📂 Load Chat Log Data")
st.info("💡 **Editor Workflow:** To analyze a Twitch VOD, use [TwitchDownloader](https://github.com/Lay295/TwitchDownloader) to export the chat log into a `.txt` file, then drop it right below.")

uploaded_file = st.file_uploader("Upload chat log (.txt)", type=["txt"])

content = None
if uploaded_file is not None:
    content = uploaded_file.getvalue().decode("utf-8", errors="ignore").splitlines()

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
        st.dataframe(df_peaks, use_column_width=True, hide_index=True)

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
        st.warning("Could not find valid timestamps. Check that your chat text file follows the standard timestamp format (e.g., [HH:MM:SS]).")

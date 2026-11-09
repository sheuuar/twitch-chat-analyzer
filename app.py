import streamlit as st
from collections import defaultdict
import pandas as pd
from chat_downloader import ChatDownloader

# Page Configuration
st.set_page_config(page_title="Stream Chat Highlight Analyzer", page_icon="🔥", layout="wide")

# Sidebar settings for user control
st.sidebar.header("⚙️ Analyzer Settings")
top_n = st.sidebar.slider("Number of highlights to display", min_value=5, max_value=50, value=25)
time_window = st.sidebar.slider("Deduplication window (minutes)", min_value=1, max_value=5, value=2)

st.title("🔥 Stream Chat Highlight Analyzer")
st.markdown("Extract unique VOD peak timestamps instantly by uploading a chat log or pasting a Twitch VOD URL.")

# Option Selection for Input
input_method = st.radio("Choose Input Method:", ["Upload Chat Log (.txt)", "Paste Twitch VOD Link"])

content = None
raw_chat_text = ""

if input_method == "Upload Chat Log (.txt)":
    uploaded_file = st.file_uploader("Upload chat log (.txt)", type=["txt"])
    if uploaded_file is not None:
        raw_bytes = uploaded_file.getvalue()
        raw_chat_text = raw_bytes.decode("utf-8", errors="ignore")
        content = raw_chat_text.splitlines()

else:
    vod_url = st.text_input("Paste Twitch VOD URL (e.g., https://www.twitch.tv/videos/...)")
    if vod_url:
        try:
            with st.spinner("Fetching and downloading chat log from VOD URL... Please wait."):
                # Correctly initialize chat downloader without invalid keyword arguments
                chat = ChatDownloader().get_chat(vod_url)
                
                extracted_lines = []
                for message in chat:
                    hours = int(message.get('hours', 0))
                    minutes = int(message.get('minutes', 0))
                    seconds = int(message.get('seconds', 0))
                    
                    time_str = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
                    msg_text = message.get('message', '')
                    
                    extracted_lines.append(f"{time_str} {msg_text}")
                
                content = extracted_lines
                raw_chat_text = "\n".join(content)
                st.success(f"Successfully downloaded {len(content):,} messages from the link!")
                
                # Dedicated button to download the chatlog text file right from the link!
                st.download_button(
                    label="📥 Download Chat Log (.txt)",
                    data=raw_chat_text,
                    file_name="twitch_chat_log.txt",
                    mime="text/plain"
                )
        except Exception as e:
            st.error(f"Could not fetch chat from this URL. Make sure it's a public VOD link. (Error: {e})")

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
        
        df_peaks = pd.DataFrame(table_data)
        st.dataframe(df_peaks, use_container_width=True, hide_index=True)

        st.download_button(
            label="📥 Download Highlight Report (.txt)",
            data=report_text,
            file_name="highlight_report.txt",
            mime="text/plain"
        )
    else:
        st.warning("Could not find valid timestamps from this source. Try a different link.")

import streamlit as st
from collections import defaultdict
import pandas as pd
import requests

# Page Configuration
st.set_page_config(page_title="Stream Chat Highlight Analyzer", page_icon="🔥", layout="wide")

# Sidebar settings for user control
st.sidebar.header("⚙️ Analyzer Settings")
top_n = st.sidebar.slider("Number of highlights to display", min_value=5, max_value=50, value=25)
time_window = st.sidebar.slider("Deduplication window (minutes)", min_value=1, max_value=5, value=2)

st.title("🔥 Stream Chat Highlight Analyzer")
st.markdown("Extract unique VOD peak timestamps by pasting a Twitch VOD link or uploading your chat log file.")

# Option Selection for Input
input_method = st.radio("Choose Input Method:", ["Paste Twitch VOD Link", "Upload Chat Log (.txt)"])

content = None

if input_method == "Paste Twitch VOD Link":
    vod_url = st.text_input("Paste Twitch VOD URL (e.g., https://www.twitch.tv/videos/...)")
    
    if vod_url:
        if st.button("🚀 Download & Analyze VOD Chat"):
            try:
                # Extract Video ID from standard Twitch URLs
                clean_url = vod_url.split("?")[0]
                video_id = clean_url.rstrip("/").split("/")[-1]
                
                if video_id.isdigit():
                    with st.spinner(f"Fetching chat comments for VOD ID {video_id} from Twitch..."):
                        # Public Twitch Helix/v5 comment endpoint
                        api_url = f"https://api.twitch.tv/v5/videos/{video_id}/comments?content_offset_seconds=0"
                        headers = {"Client-ID": "kimne78kx3ncx6brgo4mv6wbc591hu"}
                        
                        response = requests.get(api_url, headers=headers)
                        
                        if response.status_code == 200:
                            data = response.json()
                            comments = data.get("comments", [])
                            
                            extracted_lines = []
                            for comment in comments:
                                offset = comment.get("content_offset_seconds", 0)
                                hours = int(offset // 3600)
                                minutes = int((offset % 3600) // 60)
                                seconds = int(offset % 60)
                                time_str = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
                                
                                message_body = comment.get("message", {}).get("body", "")
                                extracted_lines.append(f"{time_str} {message_body}")
                                
                            content = extracted_lines
                            st.success(f"Successfully downloaded and processed {len(content):,} messages from the VOD link!")
                        else:
                            st.error("Twitch restricted direct fetching for this video. Use the 'Upload Chat Log (.txt)' option instead!")
                else:
                    st.warning("Please enter a valid Twitch VOD URL ending in the video ID number.")
            except Exception as e:
                st.error(f"Error downloading chat: {e}")

else:
    uploaded_file = st.file_uploader("Upload chat log (.txt)", type=["txt"])
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
        st.warning("Could not find valid timestamps from this source.")

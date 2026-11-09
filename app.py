import streamlit as st
from collections import defaultdict
import pandas as pd
import subprocess
import json
import os

# Page Configuration
st.set_page_config(page_title="Stream Chat Highlight Analyzer", page_icon="🔥", layout="wide")

# Sidebar settings for user control
st.sidebar.header("⚙️ Analyzer Settings")
top_n = st.sidebar.slider("Number of highlights to display", min_value=5, max_value=50, value=25)
time_window = st.sidebar.slider("Deduplication window (minutes)", min_value=1, max_value=5, value=2)

st.title("🔥 Stream Chat Highlight Analyzer")
st.markdown("Download a chat log from a Twitch VOD link, or upload your chat log file directly.")

# Option Selection for Input
input_method = st.radio("Choose Input Method:", ["Download Chat Log from VOD Link", "Upload Chat Log (.txt)"])

content = None

if input_method == "Download Chat Log from VOD Link":
    vod_url = st.text_input("Paste Twitch VOD URL (e.g., https://www.twitch.tv/videos/...)")
    
    if vod_url:
        if st.button("🚀 Fetch & Generate Chat Log"):
            with st.spinner("Downloading chat log from Twitch... Please wait."):
                try:
                    output_template = "twitch_chat_temp"
                    
                    # Correctly tell yt-dlp to write chat subtitles/comments
                    subprocess.run([
                        "yt-dlp", 
                        "--skip-download", 
                        "--write-subs", 
                        "--sub-format", "json", 
                        "--output", output_template, 
                        vod_url
                    ], check=True, capture_output=True)
                    
                    # Find the generated chat json file
                    chat_json_file = None
                    for file in os.listdir("."):
                        if file.startswith(output_template) and file.endswith(".json"):
                            chat_json_file = file
                            break
                    
                    if chat_json_file:
                        with open(chat_json_file, "r", encoding="utf-8") as f:
                            chat_data = json.load(f)
                        
                        extracted_lines = []
                        comments = chat_data.get("comments", [])
                        for comment in comments:
                            offset = comment.get("content_offset_seconds", 0)
                            hours = int(offset // 3600)
                            minutes = int((offset % 3600) // 60)
                            seconds = int(offset % 60)
                            time_str = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
                            
                            message_body = comment.get("message", {}).get("body", "")
                            extracted_lines.append(f"{time_str} {message_body}")
                        
                        raw_chat_text = "\n".join(extracted_lines)
                        
                        # Clean up temporary file
                        os.remove(chat_json_file)
                        
                        if len(extracted_lines) > 0:
                            st.success(f"Successfully generated chat log with {len(extracted_lines):,} messages!")
                            
                            # Provide the download button for the user to save the chat log file
                            st.download_button(
                                label="📥 Download Extracted Chat Log (.txt)",
                                data=raw_chat_text,
                                file_name="twitch_chat_log.txt",
                                mime="text/plain"
                            )
                        else:
                            st.warning("Chat file generated, but no comment entries were found for this VOD.")
                    else:
                        st.error("Could not fetch chat logs for this link. Make sure it's a valid public VOD URL.")
                except Exception as e:
                    st.error(f"Error fetching chat: {e}")

else:
    uploaded_file = st.file_uploader("Upload chat log (.txt)", type=["txt"])
    if uploaded_file is not None:
        content = uploaded_file.getvalue().decode("utf-8", errors="ignore").splitlines()

# If user uploaded a file manually, process it for highlights
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

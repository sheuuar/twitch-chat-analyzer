import streamlit as st
from collections import defaultdict
import pandas as pd
import os

# Safe import for moviepy with fallback state
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except Exception:
    MOVIEPY_AVAILABLE = False

# Page Configuration
st.set_page_config(
    page_title="Stream Chat Highlight & Clip Analyzer", 
    page_icon="🔥", 
    layout="wide"
)

# Custom CSS injection for modern SaaS landing-page styling & crisp image rendering
st.markdown("""
    <style>
        .hero-title {
            font-size: 3.2rem;
            font-weight: 900;
            color: #ffffff;
            letter-spacing: -1px;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .hero-subtitle {
            color: #9ca3af;
            font-size: 1.25rem;
            text-align: center;
            margin-bottom: 2.5rem;
        }
        .feature-card {
            background-color: #18181b;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #27272a;
            text-align: center;
            height: 100%;
        }
        .feature-title {
            color: #ffffff;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .feature-desc {
            color: #a1a1aa;
            font-size: 0.9rem;
        }
        img {
            border-radius: 12px;
            image-rendering: -webkit-optimize-contrast;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar settings for user control (Clean & Minimal)
st.sidebar.header("⚙️ Analyzer Parameters")
top_n = st.sidebar.slider("Number of highlights to display", min_value=5, max_value=50, value=25)
time_window = st.sidebar.slider("Deduplication window (minutes)", min_value=1, max_value=5, value=2)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Quick Guides")
st.sidebar.markdown("1. **Chat Analyzer:** Export chat via [TwitchDownloader](https://github.com/Lay295/TwitchDownloader) and upload log above.\n2. **Video Cutter:** Paste peak timestamps into the editor below to slice clips.")

# --- PRIMARY BANNER IMAGE AT THE TOP ---
st.image("https://i.imgur.com/pBPB0dC.jpeg", use_container_width=True)
st.divider()

# Hero Section Header
st.markdown('<p class="hero-title">🔥 Stream Chat Highlight Analyzer</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Automated volume-spike detection & video clipping to find elite VOD moments instantly.</p>', unsafe_allow_html=True)

# Feature Grid
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.markdown("""
        <div class="feature-card">
            <div class="feature-title">⚡ Instant Spike Detection</div>
            <div class="feature-desc">Scans tens of thousands of chat messages in milliseconds to map exact engagement spikes.</div>
        </div>
    """, unsafe_allow_html=True)
with col_f2:
    st.markdown("""
        <div class="feature-card">
            <div class="feature-title">🎯 Smart Deduplication</div>
            <div class="feature-desc">Groups close timestamps together so you get clean, distinct highlights for your timeline.</div>
        </div>
    """, unsafe_allow_html=True)
with col_f3:
    st.markdown("""
        <div class="feature-card">
            <div class="feature-title">✂️ Video Clip Editor</div>
            <div class="feature-desc">Trim VOD segments directly into standalone MP4 files for TikTok and YouTube Shorts.</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- SECONDARY IMAGE DISPLAY ---
st.image("https://i.imgur.com/QdxrWML.png", use_container_width=True)
st.markdown("<br>", unsafe_allow_html=True)

# Requirements & Workflow Instructions Box (Chat Log)
with st.expander("📖 How to Get Your Twitch Chat Log (Click to view guide)", expanded=True):
    st.markdown("""
    ### Requirements & Workflow:
    Because Twitch blocks cloud servers from downloading live VOD chat logs automatically, follow these quick steps:
    1. **Download the tool:** Get the free, open-source desktop app [TwitchDownloader](https://github.com/Lay295/TwitchDownloader).
    2. **Export Chat:** Paste your Twitch VOD URL into TwitchDownloader and export the chat log as a standard `.txt` file.
    3. **Upload & Analyze:** Drop your exported `.txt` chat log file into the uploader below to instantly extract top timestamps.
    """)

st.markdown("---")

# Main File Upload Section
st.markdown("### 📂 Load Chat Log Data")
uploaded_file = st.file_uploader("Upload your Twitch chat log (.txt)", type=["txt"])

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
        st.warning("Could not find valid timestamps. Check that your chat text file follows the standard timestamp format (e.g., [HH:MM:SS]).")

# ==========================================
# ✂️ DEDICATED MAIN PAGE CLIP EDITOR SECTION
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <h2 style="color: #ffffff;">✂️ Video Clip Editor</h2>
        <p style="color: #9ca3af;">Transform your raw VOD files into crisp vertical clips or highlights instantly.</p>
    </div>
""", unsafe_allow_html=True)

# Video Editor Workflow Guide Box
with st.expander("📖 How to Use the Video Clip Editor (Click to view guide)", expanded=True):
    st.markdown("""
    ### Requirements & Workflow:
    Turn your detected chat peaks into ready-to-publish short-form videos in seconds:
    1. **Upload Raw VOD:** Drop your downloaded full-stream `.mp4` or `.mov` file into the video uploader.
    2. **Set Duration & Timestamp:** Adjust your preferred clip length slider, then copy a peak timestamp from your chat analysis above (format: `HH:MM:SS`).
    3. **Cut & Export:** Click **Cut & Export MP4 Clip** to automatically slice out the exact highlight, preview it live, and download your clean MP4 file.
    """)

with st.container():
    col_edit1, col_edit2 = st.columns([2, 1])
    
    with col_edit1:
        uploaded_video = st.file_uploader("Upload raw VOD video file (.mp4)", type=["mp4", "mov"], key="editor_video_upload")
        
    with col_edit2:
        clip_duration = st.slider("Clip Duration (seconds)", min_value=10, max_value=60, value=30, key="editor_duration_slider")

    if uploaded_video is not None:
        video_filename = "temp_vod.mp4"
        with open(video_filename, "wb") as f:
            f.write(uploaded_video.getbuffer())
        
        st.success("✅ VOD loaded and ready for editing!")
        
        # Timestamp input for cutting
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            clip_time_input = st.text_input("Enter Timestamp to Clip (Format: HH:MM:SS)", value="00:00:00")
        
        with col_t2:
            st.markdown("<br>", unsafe_allow_html=True)
            generate_btn = st.button("🎬 Cut & Export MP4 Clip", use_container_width=True)
        
        if generate_btn:
            if not MOVIEPY_AVAILABLE:
                st.error("⚠️ Video processing libraries are currently initializing or unavailable in this cloud container environment. For heavy video editing, we recommend running this Streamlit app locally on your machine where local FFmpeg binaries are accessible.")
            else:
                try:
                    h, m, s = map(int, clip_time_input.split(":"))
                    target_sec = h * 3600 + m * 60 + s
                    
                    start_time = max(0, target_sec - 5) # 5 seconds buffer before spike
                    end_time = target_sec + clip_duration
                    
                    output_clip_name = f"highlight_{clip_time_input.replace(':', '_')}.mp4"
                    
                    with st.spinner("Processing your clip... Please wait."):
                        with VideoFileClip(video_filename) as video:
                            clipped = video.subclip(start_time, min(end_time, video.duration))
                            clipped.write_videofile(output_clip_name, codec="libx264", audio_codec="aac", logger=None)
                        
                        st.success("🎉 Clip generated successfully!")
                        st.video(output_clip_name)
                        
                        with open(output_clip_name, "rb") as file_to_download:
                            st.download_button(
                                label="📥 Download Trimmed MP4 File",
                                data=file_to_download,
                                file_name=output_clip_name,
                                mime="video/mp4"
                            )
                except Exception as e:
                    st.error(f"Error processing video file or timestamp format. Details: {e}")

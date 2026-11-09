import streamlit as st
from collections import defaultdict

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
        st.success(f"Successfully processed {valid_lines} chat messages!")
        
        sorted_peaks = sorted(minute_counts.items(), key=lambda x: x[1], reverse=True)
        
        st.subheader("Top 25 Unique VOD Peak Timestamps:")
        shown_blocks = set()
        count_printed = 0

        report_text = "🔥 TOP 25 UNIQUE VOD PEAK TIMESTAMPS:\n\n"

        for minute_mark, count in sorted_peaks:
            if any(abs(minute_mark - existing) <= 2 for existing in shown_blocks):
                continue
                
            hrs = minute_mark // 60
            mins = minute_mark % 60
            
            line_str = f"VOD Time: {hrs:02d}:{mins:02d}:00 — {count} messages"
            st.markdown(f"- **{line_str}**")
            report_text += f"- {line_str}\n"
            
            shown_blocks.add(minute_mark)
            count_printed += 1
            if count_printed >= 25:
                break

        # --- ADDED: DOWNLOAD BUTTON ---
        st.download_button(
            label="📥 Download Report (.txt)",
            data=report_text,
            file_name="highlight_report.txt",
            mime="text/plain"
        )
    else:
        st.warning("Could not find valid timestamps. Check your chat text file format.")

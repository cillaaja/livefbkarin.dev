import sys
import subprocess
import threading
import time
import os
import streamlit.components.v1 as components

# Install streamlit jika belum ada
try:
    import streamlit as st
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
    import streamlit as st


def run_ffmpeg(video_path, stream_key, is_shorts, log_callback):
    output_url = f"rtmps://live-api-s.facebook.com:443/rtmp/{stream_key}"
    scale_filter = "-vf scale=720:1280" if is_shorts else "-vf scale=1280:720"

    cmd = [
        "ffmpeg", "-re", "-stream_loop", "-1", "-i", video_path,
        "-c:v", "libx264", "-preset", "veryfast", "-b:v", "2500k",
        "-maxrate", "2500k", "-bufsize", "5000k",
        "-g", "60", "-keyint_min", "60",
        "-c:a", "aac", "-b:a", "128k",
        *scale_filter.split(),
        "-f", "flv", output_url
    ]

    log_callback(f"Menjalankan: {' '.join(cmd)}")
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            log_callback(line.strip())
        process.wait()
    except Exception as e:
        log_callback(f"Error: {e}")
    finally:
        log_callback("Streaming selesai atau dihentikan.")


def main():
    st.set_page_config(page_title="Live ke Facebook", page_icon="📺", layout="wide")
    st.title("🎥 Live Streaming ke Facebook")

    st.markdown("Gunakan video lokal atau unggah, lalu masukkan Facebook Stream Key untuk mulai.")

    show_ads = st.checkbox("Tampilkan Iklan", value=False)
    if show_ads:
        components.html(
            """
            <div style="background:#f0f2f6;padding:20px;border-radius:10px;text-align:center">
                <script type='text/javascript' 
                        src='//pl26562103.profitableratecpm.com/28/f9/95/28f9954a1d5bbf4924abe123c76a68d2.js'>
                </script>
                <p style="color:#888">Iklan akan muncul di sini</p>
            </div>
            """,
            height=300
        )

    video_files = [f for f in os.listdir('.') if f.endswith(('.mp4', '.flv'))]
    selected_video = st.selectbox("Pilih video", video_files) if video_files else None

    uploaded_file = st.file_uploader("Atau upload video baru (mp4/flv - codec H264/AAC)", type=['mp4', 'flv'])
    if uploaded_file:
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.read())
        st.success("Video berhasil diupload!")
        video_path = uploaded_file.name
    elif selected_video:
        video_path = selected_video
    else:
        video_path = None

    stream_key = st.text_input("Masukkan Facebook Stream Key", type="password")
    is_shorts = st.checkbox("Mode Shorts (720x1280)")

    log_placeholder = st.empty()
    logs = []

    def log_callback(msg):
        logs.append(msg)
        try:
            log_placeholder.text("\n".join(logs[-20:]))
        except:
            print(msg)

    if 'ffmpeg_thread' not in st.session_state:
        st.session_state['ffmpeg_thread'] = None

    if st.button("Mulai Streaming"):
        if not video_path or not stream_key:
            st.error("Video dan Stream Key wajib diisi!")
        else:
            st.session_state['ffmpeg_thread'] = threading.Thread(
                target=run_ffmpeg,
                args=(video_path, stream_key, is_shorts, log_callback),
                daemon=True
            )
            st.session_state['ffmpeg_thread'].start()
            st.success("🚀 Streaming ke Facebook dimulai!")

    if st.button("Hentikan Streaming"):
        os.system("pkill ffmpeg")
        st.warning("🛑 Streaming dihentikan!")

    log_placeholder.text("\n".join(logs[-20:]))

if __name__ == '__main__':
    main()

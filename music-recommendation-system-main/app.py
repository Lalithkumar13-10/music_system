import streamlit as st
import datetime
import json
import pandas as pd
import hashlib
from PIL import Image

import config
import emotion_detector
import music_recommender

# Set Streamlit Page Config
st.set_page_config(
    page_title="MoodTune - Emotion Based Music Recommendations",
    page_icon="🎶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- SESSION STATE INITIALIZATION -----------------
if "burst_frames" not in st.session_state:
    st.session_state.burst_frames = []
if "pending_multi_face" not in st.session_state:
    st.session_state.pending_multi_face = []
if "recommended_tracks" not in st.session_state:
    st.session_state.recommended_tracks = []
if "mode_used" not in st.session_state:
    st.session_state.mode_used = ""
if "session_history" not in st.session_state:
    st.session_state.session_history = []
if "recommended_track_ids" not in st.session_state:
    st.session_state.recommended_track_ids = set()
if "selected_emotion" not in st.session_state:
    st.session_state.selected_emotion = ""
if "selected_confidence" not in st.session_state:
    st.session_state.selected_confidence = 0.0
if "last_processed_frame" not in st.session_state:
    st.session_state.last_processed_frame = ""

# ----------------- AGGREGATION & BURST LOGIC -----------------
def aggregate_burst(burst_frames):
    """
    Combines a list of detections into a single final emotion and confidence score.
    Uses majority voting. In case of a tie, selects the emotion with the highest
    average confidence score.
    """
    from collections import Counter
    emotions = [f["emotion"] for f in burst_frames]
    counts = Counter(emotions)
    max_count = max(counts.values())
    candidates = [emo for emo, count in counts.items() if count == max_count]

    if len(candidates) == 1:
        winner = candidates[0]
    else:
        # Tie-breaker: select the candidate emotion with the highest average confidence
        winner = None
        best_avg_conf = -1.0
        for cand in candidates:
            confs = [f["confidence"] for f in burst_frames if f["emotion"] == cand]
            avg_conf = sum(confs) / len(confs)
            if avg_conf > best_avg_conf:
                best_avg_conf = avg_conf
                winner = cand

    # Average confidence of the winner's frames
    winner_confs = [f["confidence"] for f in burst_frames if f["emotion"] == winner]
    avg_winner_conf = sum(winner_confs) / len(winner_confs)

    return winner, avg_winner_conf

def process_single_frame(frame_detection):
    """Adds a single detection to the burst state, and aggregates if complete."""
    st.session_state.burst_frames.append({
        "emotion": frame_detection["emotion"],
        "confidence": frame_detection["confidence"],
        "cropped_image": frame_detection["cropped_image"]
    })

    if len(st.session_state.burst_frames) >= 3:
        winner, avg_conf = aggregate_burst(st.session_state.burst_frames)
        
        # Trigger recommendations
        tracks, mode = music_recommender.get_music_recommendations(
            emotion=winner,
            exclude_ids=st.session_state.recommended_track_ids,
            limit=5
        )
        
        # Update Session State
        st.session_state.selected_emotion = winner
        st.session_state.selected_confidence = avg_conf
        st.session_state.recommended_tracks = tracks
        st.session_state.mode_used = mode
        
        # Store recommended IDs in exclusion list
        for t in tracks:
            st.session_state.recommended_track_ids.add(t["id"])
            
        # Log to Session History
        st.session_state.session_history.append({
            "emotion": winner,
            "confidence": avg_conf,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Clear current burst frames for the next scan
        st.session_state.burst_frames = []

# ----------------- PREMIUM UI / THEMING -----------------
# Determine theme styling based on the currently selected emotion
active_emotion = st.session_state.selected_emotion or "neutral"
active_conf = config.EMOTION_CONFIGS.get(active_emotion, config.EMOTION_CONFIGS["neutral"])
theme_color = active_conf["color"]
bg_gradient = active_conf["bg_gradient_dark"]

# Inject styling for custom CSS components
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Outfit:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    h1, h2, h3, .brand-title {{
        font-family: 'Outfit', sans-serif;
    }}
    
    /* App Header Styling */
    .app-header {{
        background: linear-gradient(135deg, #111111 0%, #1a1a1a 100%);
        border-bottom: 2px solid {theme_color};
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 24px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }}
    
    .header-title {{
        color: #FFFFFF;
        margin: 0;
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(90deg, #FFFFFF 0%, {theme_color} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .header-subtitle {{
        color: #B3B3B3;
        margin: 8px 0 0 0;
        font-size: 1.1rem;
        font-weight: 300;
    }}
    
    /* Glassmorphic card styling */
    .premium-card {{
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }}
    
    /* Song card styling */
    .song-card {{
        background: rgba(255, 255, 255, 0.03);
        border-left: 5px solid {theme_color};
        border-top: 1px solid rgba(255, 255, 255, 0.04);
        border-right: 1px solid rgba(255, 255, 255, 0.04);
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s;
    }}
    .song-card:hover {{
        transform: translateY(-2px);
        background: rgba(255, 255, 255, 0.06);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    }}
    .song-title {{
        color: #FFFFFF;
        font-size: 1.2rem;
        font-weight: 700;
        margin: 0;
    }}
    .song-artist {{
        color: #B3B3B3;
        font-size: 0.95rem;
        margin: 2px 0 10px 0;
    }}
    
    /* Mode Badge */
    .mode-badge {{
        background-color: {theme_color}18;
        color: {theme_color};
        border: 1px solid {theme_color}44;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR CONTENT -----------------
with st.sidebar:
    st.markdown("<div style='text-align: center; margin-bottom: 20px;'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color: {theme_color}; margin: 0; font-family: Outfit;'>MoodTune Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Greeting based on local time
    current_hour = datetime.datetime.now().hour
    if current_hour < 12:
        greeting = "Good Morning! 🌅"
    elif 12 <= current_hour < 18:
        greeting = "Good Afternoon! 🌞"
    else:
        greeting = "Good Evening! 🌙"
    st.subheader(greeting)
    
    st.markdown("---")
    
    # Visual Session History
    st.markdown("### 📈 Session Mood Trend")
    if st.session_state.session_history:
        chart_data = []
        emotion_numeric_map = {"sad": 1, "fear": 2, "anger": 3, "neutral": 4, "happy": 5}
        for idx, item in enumerate(st.session_state.session_history):
            val = emotion_numeric_map.get(item["emotion"], 4)
            chart_data.append({
                "Reading": idx + 1,
                "Mood Index": val,
                "Emotion": item["emotion"].capitalize()
            })
        df = pd.DataFrame(chart_data)
        
        # Render Line Chart
        st.line_chart(df.set_index("Reading")[["Mood Index"]])
        
        # Display Text Log
        st.markdown("#### 🗂 Recent Scans")
        for item in reversed(st.session_state.session_history[-5:]):
            conf_percent = int(item["confidence"] * 100)
            conf_str = config.EMOTION_CONFIGS.get(item["emotion"], {}).get("emoji", "😐")
            st.markdown(f"**{conf_str} {item['emotion'].capitalize()}** ({conf_percent}%) — *{item['timestamp'].split(' ')[1]}*")
    else:
        st.info("No scans in this session yet. Take 3 photos to record your first mood!")

    st.markdown("---")

    # Feedback Section
    st.markdown("### 🎤 Feedback & Suggestions")
    feedback_text = st.text_area("How did we do? Enter your thoughts:", height=100, placeholder="Songs matched my mood perfectly!...")
    
    if st.button("Submit Feedback", use_container_width=True):
        if feedback_text.strip():
            entry = {
                "feedback": feedback_text,
                "timestamp": datetime.datetime.now().isoformat(),
                "detected_emotion": st.session_state.selected_emotion or "none",
                "confidence": st.session_state.selected_confidence
            }
            try:
                with open(config.FEEDBACK_FILE_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
                st.success("Thank you for your feedback! It was saved locally. 🙏")
            except Exception as e:
                st.error(f"Error saving feedback: {e}")
        else:
            st.warning("Please write something before submitting.")

# ----------------- MAIN APP UI -----------------
# Header banner
st.markdown(f"""
<div class="app-header">
    <h1 class="header-title">MoodTune</h1>
    <p class="header-subtitle">Facetalk to Soundtracks — Webcam Emotion Detected Music Recommendation</p>
</div>
""", unsafe_allow_html=True)

# Layout Setup
col_cam, col_rec = st.columns([1, 1], gap="large")

with col_cam:
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("### 📷 Webcam Capture")
    st.markdown("Capture a burst of **3 photos** to analyze your emotion accurately.")

    # Webcam camera input
    camera_file = st.camera_input("Smile, frown, or look relaxed and click capture!")
    
    # Process capture
    if camera_file is not None:
        file_bytes = camera_file.getvalue()
        file_hash = hashlib.md5(file_bytes).hexdigest()
        
        # Check if this is a newly taken picture or if we've already processed it
        if st.session_state.last_processed_frame != file_hash:
            st.session_state.last_processed_frame = file_hash
            
            with st.spinner("Analyzing facial expressions..."):
                detections = emotion_detector.detect_faces_and_emotions(camera_file)
                
                if not detections:
                    st.warning("⚠️ No face was confidently detected. Please ensure you are centered, looking at the camera, and in a well-lit room.")
                elif len(detections) > 1:
                    # Stash multiple detections for manual resolution
                    st.session_state.pending_multi_face = detections
                else:
                    # Single face detected — proceed immediately
                    process_single_frame(detections[0])
                    st.rerun()

    # Handle unresolved multiple faces
    if st.session_state.pending_multi_face:
        st.markdown("---")
        st.warning("👥 **Multiple faces detected!** Please select which face is yours:")
        
        multi_cols = st.columns(len(st.session_state.pending_multi_face))
        for idx, face in enumerate(st.session_state.pending_multi_face):
            with multi_cols[idx]:
                st.image(face["cropped_image"], use_container_width=True)
                st.write(f"Emotion: **{face['emotion'].capitalize()}**")
                st.write(f"Confidence: **{int(face['confidence'] * 100)}%**")
                
                if st.button("This is my face", key=f"select_face_{idx}", use_container_width=True):
                    selected_face = st.session_state.pending_multi_face[idx]
                    st.session_state.pending_multi_face = []
                    process_single_frame(selected_face)
                    st.rerun()
                    
        if st.button("Discard Frame", use_container_width=True, type="secondary"):
            st.session_state.pending_multi_face = []
            st.rerun()

    # Progress bar and status of current burst
    st.markdown("---")
    num_frames = len(st.session_state.burst_frames)
    
    if num_frames > 0:
        st.progress(num_frames / 3.0)
        st.info(f"Captured: **{num_frames} of 3** frames for the current session. Take another photo!")
        
        # Display thumbnails of burst captures so far
        st.markdown("#### Captured frames:")
        thumb_cols = st.columns(3)
        for idx, frame in enumerate(st.session_state.burst_frames):
            with thumb_cols[idx]:
                st.image(frame["cropped_image"], width=100, caption=f"{frame['emotion'].capitalize()}")
                
        if st.button("Reset Capture Progress", type="secondary"):
            st.session_state.burst_frames = []
            st.rerun()
    else:
        st.info("No frames currently captured. Take a photo to start a mood analysis session!")
        
    st.markdown("</div>", unsafe_allow_html=True)

with col_rec:
    if st.session_state.selected_emotion:
        emotion = st.session_state.selected_emotion
        confidence = st.session_state.selected_confidence
        tracks = st.session_state.recommended_tracks
        mode = st.session_state.mode_used
        conf_entry = config.EMOTION_CONFIGS.get(emotion, config.EMOTION_CONFIGS["neutral"])
        
        # Aesthetic Mood-Colored Container (scoped styled container wrapper)
        st.markdown(f"""
        <div style="
            background: {conf_entry['bg_gradient_dark']};
            color: #FFFFFF;
            padding: 24px;
            border-radius: 16px;
            border: 2px solid {conf_entry['color']};
            box-shadow: 0 8px 30px {conf_entry['color']}22;
            margin-bottom: 24px;
        ">
            <h2 style="margin: 0; color: {conf_entry['color']}; font-family: Outfit; font-weight: 800; font-size: 2.2rem;">
                {conf_entry['emoji']} {emotion.upper()}
            </h2>
            <div style="font-size: 1.1rem; font-weight: 600; margin-top: 4px; opacity: 0.95;">
                Detected with {int(confidence * 100)}% confidence
            </div>
            <p style="font-size: 1.05rem; margin-top: 12px; margin-bottom: 12px; opacity: 0.9; font-weight: 300;">
                {conf_entry['greeting']}
            </p>
            <div style="
                background: rgba(0, 0, 0, 0.25);
                border-left: 4px solid {conf_entry['color']};
                border-radius: 6px;
                padding: 12px;
                font-size: 0.95rem;
                line-height: 1.4;
                opacity: 0.95;
            ">
                <strong>💡 Did you know?</strong> {conf_entry['fun_fact']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        st.markdown("### 🎵 Recommended Tracks")
        
        # Display source mode as a sleek badge
        mode_label = "Local Backup Songs"
        if mode == "spotify_features":
            mode_label = "Spotify Smart recommendations (Audio Features)"
        elif mode == "spotify_search_fallback":
            mode_label = "Spotify Search Fallback"
            
        st.markdown(f"<span class='mode-badge'>{mode_label}</span>", unsafe_allow_html=True)

        # List recommended songs
        if tracks:
            for track in tracks:
                track_id = track["id"]
                track_url = track["url"]
                
                st.markdown(f"""
                <div class="song-card">
                    <div class="song-title">{track['name']}</div>
                    <div class="song-artist">by {track['artist']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Spotify Embed Player
                iframe_src = f"https://open.spotify.com/embed/track/{track_id}"
                st.markdown(f"""
                <iframe src="{iframe_src}" width="100%" height="80" frameBorder="0" allowtransparency="true" allow="encrypted-media" style="border-radius: 8px; margin-bottom: 16px;"></iframe>
                """, unsafe_allow_html=True)
        else:
            st.warning("No recommendations available for this mood.")

        # Controls to reset and start a new scan
        st.markdown("---")
        if st.button("Reset & Detect Again", use_container_width=True, type="primary"):
            st.session_state.selected_emotion = ""
            st.session_state.selected_confidence = 0.0
            st.session_state.recommended_tracks = []
            st.session_state.mode_used = ""
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Initial Dashboard / Welcome screen in column 2
        st.markdown("<div class='premium-card' style='text-align: center; padding: 60px 24px;'>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='color: {theme_color}; font-size: 4rem; margin-bottom: 10px;'>👋</h1>", unsafe_allow_html=True)
        st.markdown("### Welcome to MoodTune!")
        st.markdown("""
        How are you feeling today? Discover songs that match your mood perfectly.
        
        **How it works:**
        1. Stand in front of your camera with decent lighting.
        2. Click **Take Photo** on the webcam capture panel.
        3. Capture a burst of **3 consecutive photos** to get an accurate reading (we'll run majority vote detection!).
        4. Receive customized **Spotify recommendations** matching your mood!
        
        *Ensure you have your Spotify client keys configured in `.env` for the best recommended audio features!*
        """)
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------- FOOTER -----------------
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666666; font-size: 0.85rem; padding: 10px 0;'>
    Made with ❤️ using Streamlit, YOLOv8 Face Emotion Detection, and the Spotify Web API.<br>
    © 2026 MoodTune Inc. All rights reserved.
</div>
""", unsafe_allow_html=True)

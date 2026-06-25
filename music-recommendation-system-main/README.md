# MoodTune 🎶

MoodTune is a premium Streamlit web application that detects a user's facial emotion via their webcam and recommends tailored Spotify songs matching their mood. It utilizes YOLOv8 for face detection and emotion classification, and interfaces with the Spotify Web API to pull recommendations using audio features (valence and energy).

---

## Features

1. **Reliable Emotion Detection**:
   - Captures a **3-frame burst** of webcam photos using `st.camera_input` to avoid single-frame noise.
   - Computes a majority vote or confidence-weighted average to determine the final mood.
   - Gracefully handles multiple faces by prompting the user to click and select their face from cropped columns.
   - Displays prediction confidence (e.g. `Happy — 87% confidence`).

2. **Advanced Music Matching**:
   - Maps detected emotions to targeted Spotify audio-feature ranges (`valence` and `energy`) for high-fidelity recommendation.
   - Prevents looping by keeping track of previously recommended song IDs and excluding them during the session.
   - Implements a multi-layered fallback system: if the Spotify API fails, rate-limits, or has no keys configured, the application falls back to a hand-curated local catalog (`fallback_songs.json`) containing 5 high-quality tracks per emotion.

3. **Session Experience**:
   - Logs history of `{emotion, confidence, timestamp}` for each reading.
   - Visualizes session mood progression using a dynamic line chart.
   - Scopes styled containers with custom backgrounds reflecting the detected mood (e.g. glowing gold for happy, deep calming blue for sad).
   - Collects user feedback and appends it locally to `feedback.jsonl`.

---

## Tech Stack

- **Frontend**: Streamlit
- **Deep Learning**: Ultralytics YOLOv8 (custom-trained weights `best (1).pt`)
- **APIs**: Spotipy (Spotify Web API wrapper)
- **Environment**: python-dotenv

---

## File Structure

- [app.py](app.py): Entry point. Streamlit UI, session state coordinator, burst capture, face selector, charts, and feedback form.
- [emotion_detector.py](emotion_detector.py): Loads the YOLOv8 model (cached with `@st.cache_resource`) and handles image cropping/inference.
- [music_recommender.py](music_recommender.py): Manages Spotify authentication, recommended audio-feature seeds, keyword search fallbacks, and local catalog loaders.
- [config.py](config.py): Configures paths, settings, YOLO label mappings, and mood configurations.
- [fallback_songs.json](fallback_songs.json): Curated fallback playlist database.

---

## Getting Started

### 1. Prerequisites
Ensure you have Python 3.11 or higher installed on your machine.

### 2. Place YOLO Model Weights
Make sure your custom-trained YOLO weights file is placed in the project root directory:
```
/music-recommendation system/best (1).pt
```
*Note: If your file has a different name, configure it in your `.env` file under `YOLO_MODEL_PATH`.*

### 3. Get Spotify API Credentials
1. Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Log in with your Spotify account and click **Create app**.
3. Fill in the app details:
   - **App name**: MoodTune
   - **App description**: Web app for recommending music based on facial emotion.
   - **Redirect URI**: `http://localhost:8501` (standard Streamlit port).
4. Save the app, go to **Settings**, and locate your **Client ID** and **Client Secret**.

### 4. Configure Environment Variables
Copy `.env.example` to a new file named `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in your Spotify API credentials:
```env
SPOTIFY_CLIENT_ID=your_actual_client_id_here
SPOTIFY_CLIENT_SECRET=your_actual_client_secret_here
```

### 5. Installation
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 6. Run the Application
Start the Streamlit server locally:
```bash
streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## Out of Scope & Future Enhancements

The following features are explicitly out of scope for the current version:
- **Spotify OAuth / Playlist Creation**: The app uses client-credentials authentication, meaning it doesn't log into a specific user account. Future enhancements could integrate full Spotify OAuth to allow users to directly save recommended tracks into a custom playlist on their personal profile.
- **Persistent User Accounts**: No login or registration features are built in. Session history is maintained in-memory for the current browser session.
- **Native Mobile Apps**: MoodTune is a mobile-responsive web application and doesn't require native builds.

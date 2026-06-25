import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Spotify API Credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")

# YOLO Model Configuration
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "best (1).pt")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.30"))

# Local Data Paths
FALLBACK_SONGS_PATH = os.getenv("FALLBACK_SONGS_PATH", "fallback_songs.json")
FEEDBACK_FILE_PATH = os.getenv("FEEDBACK_FILE_PATH", "feedback.jsonl")

# YOLO Custom Class Map
# Mapped classes: 0: anger, 1: fear, 2: happy, 3: neutral, 4: sad
YOLO_CLASS_MAP = {
    0: "anger",
    1: "fear",
    2: "happy",
    3: "neutral",
    4: "sad"
}

# Emotion Configurations for Recommendations and UI Styling
EMOTION_CONFIGS = {
    "happy": {
        "seed_genres": ["happy", "pop", "dance"],
        "target_valence": 0.85,
        "target_energy": 0.75,
        "fallback_query": "happy pop upbeat",
        "color": "#FFD700",  # Vibrant Gold
        "bg_gradient": "linear-gradient(135deg, #FFF9E6 0%, #FFF2CC 100%)",
        "bg_gradient_dark": "linear-gradient(135deg, #1E1A0A 0%, #2D250F 100%)",
        "emoji": "😊",
        "greeting": "Looking bright and joyful! ☀️",
        "fun_fact": "Smiling can reduce stress, lower your heart rate, and boost your immune system!"
    },
    "sad": {
        "seed_genres": ["sad", "acoustic", "rainy-day"],
        "target_valence": 0.15,
        "target_energy": 0.25,
        "fallback_query": "sad acoustic melancholic",
        "color": "#4682B4",  # Steel Blue
        "bg_gradient": "linear-gradient(135deg, #EBF3F9 0%, #D6E4F0 100%)",
        "bg_gradient_dark": "linear-gradient(135deg, #0D161F 0%, #152433 100%)",
        "emoji": "😢",
        "greeting": "It's okay to feel down. Let's find some comfort. 🌧️",
        "fun_fact": "Listening to sad music can actually evoke positive emotions and provide emotional relief."
    },
    "anger": {
        "seed_genres": ["rock", "metal", "hard-rock"],
        "target_valence": 0.25,
        "target_energy": 0.85,
        "fallback_query": "intense rock metal",
        "color": "#FF4500",  # Orange Red
        "bg_gradient": "linear-gradient(135deg, #FFEBE6 0%, #FFD6CC 100%)",
        "bg_gradient_dark": "linear-gradient(135deg, #210D07 0%, #36170E 100%)",
        "emoji": "😠",
        "greeting": "Let's channel that energy and blow off some steam! 🔥",
        "fun_fact": "High-energy, intense music like rock or metal can help process anger and lower stress levels."
    },
    "fear": {
        "seed_genres": ["ambient", "chill", "sleep"],
        "target_valence": 0.40,
        "target_energy": 0.20,
        "fallback_query": "calming ambient chill",
        "color": "#9370DB",  # Medium Purple
        "bg_gradient": "linear-gradient(135deg, #F3EBF9 0%, #E7D6F0 100%)",
        "bg_gradient_dark": "linear-gradient(135deg, #130D1F 0%, #201533 100%)",
        "emoji": "😨",
        "greeting": "Take a deep breath. Let's find some calm. 🌌",
        "fun_fact": "Ambient music with slower tempos can slow down heart rates and reduce anxiety."
    },
    "neutral": {
        "seed_genres": ["chill", "acoustic", "indie"],
        "target_valence": 0.50,
        "target_energy": 0.40,
        "fallback_query": "indie chill acoustic",
        "color": "#7F8C8D",  # Slate Gray
        "bg_gradient": "linear-gradient(135deg, #F2F4F4 0%, #E5E8E8 100%)",
        "bg_gradient_dark": "linear-gradient(135deg, #131718 0%, #212526 100%)",
        "emoji": "😐",
        "greeting": "Keeping it steady and balanced. 🧘",
        "fun_fact": "A neutral state is the perfect launching pad for clear thinking and mindful decision-making."
    }
}

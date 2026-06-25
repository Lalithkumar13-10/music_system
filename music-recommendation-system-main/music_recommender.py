import json
import random
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import config

# Helper function to get Spotify client
def _get_spotify_client(client_id: str, client_secret: str):
    """
    Creates and returns an authenticated spotipy.Spotify client.
    Returns None if credentials are missing or connection fails.
    """
    if not client_id or not client_secret:
        return None
    try:
        credentials_manager = SpotifyClientCredentials(
            client_id=client_id, 
            client_secret=client_secret
        )
        return spotipy.Spotify(client_credentials_manager=credentials_manager)
    except Exception as e:
        # Keep authentication errors silent in logs, handle gracefully
        print(f"Spotify authentication failed: {e}")
        return None

@st.cache_data(ttl=300)
def _fetch_valid_genre_seeds(client_id: str, client_secret: str):
    """
    Fetches valid recommendation seed genres from Spotify. Cached for 5 minutes.
    """
    sp = _get_spotify_client(client_id, client_secret)
    if sp is None:
        return set()
    try:
        seeds = sp.recommendation_genre_seeds()
        return set(seeds.get("genres", []))
    except Exception as e:
        print(f"Error fetching genre seeds: {e}")
        return set()

@st.cache_data(ttl=300)
def _fetch_recommendations_from_spotify(
    genres: list, 
    valence: float, 
    energy: float, 
    client_id: str, 
    client_secret: str, 
    limit: int = 20
):
    """
    Fetches recommendations from Spotify based on target valence, energy, and genres.
    Cached for 5 minutes.
    """
    sp = _get_spotify_client(client_id, client_secret)
    if sp is None:
        return []
        
    try:
        # Filter genres to only include those supported by Spotify seed genres
        valid_seeds = _fetch_valid_genre_seeds(client_id, client_secret)
        filtered_genres = [g for g in genres if g in valid_seeds]
        
        # If no valid genres, fall back to one common genre from the list that is valid
        if not filtered_genres and valid_seeds:
            for fallback_g in ["pop", "acoustic", "rock", "ambient", "chill"]:
                if fallback_g in valid_seeds:
                    filtered_genres = [fallback_g]
                    break
        
        if not filtered_genres:
            # No valid seed genres found at all, recommendation API cannot run
            return []

        # Request recommendations from Spotify
        results = sp.recommendations(
            seed_genres=filtered_genres[:5],  # Max 5 seed genres allowed
            target_valence=valence,
            target_energy=energy,
            limit=limit
        )
        
        tracks = []
        for track in results.get("tracks", []):
            tracks.append({
                "name": track["name"],
                "artist": track["artists"][0]["name"] if track["artists"] else "Unknown Artist",
                "id": track["id"],
                "url": track["external_urls"].get("spotify", f"https://open.spotify.com/track/{track['id']}")
            })
        return tracks
    except Exception as e:
        print(f"Spotify Recommendations API call failed: {e}")
        return []

@st.cache_data(ttl=300)
def _fetch_search_from_spotify(query: str, client_id: str, client_secret: str, limit: int = 20):
    """
    Searches for tracks on Spotify based on a keyword query.
    Cached for 5 minutes.
    """
    sp = _get_spotify_client(client_id, client_secret)
    if sp is None:
        return []
        
    try:
        results = sp.search(q=query, limit=limit, type="track")
        tracks_raw = results.get("tracks", {}).get("items", [])
        
        tracks = []
        for track in tracks_raw:
            tracks.append({
                "name": track["name"],
                "artist": track["artists"][0]["name"] if track["artists"] else "Unknown Artist",
                "id": track["id"],
                "url": track["external_urls"].get("spotify", f"https://open.spotify.com/track/{track['id']}")
            })
        return tracks
    except Exception as e:
        print(f"Spotify Search API call failed: {e}")
        return []

def _get_local_fallbacks(emotion: str, exclude_ids: set, limit: int = 5):
    """
    Loads fallback songs from local fallback_songs.json, filtering out already seen IDs.
    """
    try:
        with open(config.FALLBACK_SONGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        all_songs = data.get(emotion, [])
        # Filter out previously recommended songs
        filtered_songs = [s for s in all_songs if s["id"] not in exclude_ids]
        
        # If we filtered everything out, reset and reuse to avoid dead-ending
        if not filtered_songs:
            filtered_songs = all_songs
            
        random.shuffle(filtered_songs)
        return filtered_songs[:limit]
    except Exception as e:
        # Extreme emergency fallback if JSON is corrupted/missing
        print(f"Failed to read fallback JSON: {e}")
        emergency = {
            "name": "Don't Stop Believin'",
            "artist": "Journey",
            "id": "4O90gU7c47dcc3n9oQd3fT",
            "url": "https://open.spotify.com/track/4O90gU7c47dcc3n9oQd3fT"
        }
        return [emergency] * limit

def get_music_recommendations(emotion: str, exclude_ids: set, limit: int = 5):
    """
    Retrieves music recommendations for a given emotion.
    Tries Spotify Recommendations first, falls back to Spotify Search, and
    ultimately falls back to local JSON files if Spotify is unavailable or fails.
    """
    # 1. Clean emotion key to match YOLO map
    emotion = emotion.lower().strip()
    if emotion not in config.EMOTION_CONFIGS:
        emotion = "neutral"

    conf = config.EMOTION_CONFIGS[emotion]
    client_id = config.SPOTIFY_CLIENT_ID
    client_secret = config.SPOTIFY_CLIENT_SECRET

    # Check if Spotify API keys are provided
    api_available = bool(client_id and client_secret)
    tracks = []
    mode_used = "local_fallback"

    if api_available:
        # Step A: Attempt Recommendations based on valence/energy
        try:
            spotify_recommendations = _fetch_recommendations_from_spotify(
                genres=conf["seed_genres"],
                valence=conf["target_valence"],
                energy=conf["target_energy"],
                client_id=client_id,
                client_secret=client_secret,
                limit=30  # Request more to allow filtering out duplicates
            )
            filtered = [t for t in spotify_recommendations if t["id"] not in exclude_ids]
            if filtered:
                tracks = filtered[:limit]
                mode_used = "spotify_features"
        except Exception:
            pass

        # Step B: Fallback to Keyword Search if Recommendations failed or yielded nothing
        if not tracks:
            try:
                spotify_search = _fetch_search_from_spotify(
                    query=conf["fallback_query"],
                    client_id=client_id,
                    client_secret=client_secret,
                    limit=30
                )
                filtered = [t for t in spotify_search if t["id"] not in exclude_ids]
                if filtered:
                    tracks = filtered[:limit]
                    mode_used = "spotify_search_fallback"
            except Exception:
                pass

    # Step C: Fall back to local JSON songs if API is unavailable or search returned nothing
    if not tracks:
        tracks = _get_local_fallbacks(emotion, exclude_ids, limit=limit)
        mode_used = "local_fallback"

    return tracks, mode_used

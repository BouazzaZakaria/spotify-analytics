# extract.py
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from dotenv import load_dotenv
import pandas as pd
import time

load_dotenv()

SCOPES = "user-top-read user-library-read user-read-recently-played"


def get_spotify_client():
    return spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(),
        requests_timeout=15,
        retries=3
    )


# -------------------------------------------------------
# 1. TOP TRACKS (with batch-fetched audio features)
# -------------------------------------------------------
def extract_playlist_tracks(sp, playlist_id="37i9dQZEVXbMDoHDwVN2tF"):
    """Default: Spotify Top 50 Global (public playlist)."""
    results = sp.playlist_items(playlist_id, limit=100)
    rows = []
    for i, item in enumerate(results["items"]):
        track = item["track"]
        rows.append({
            "rank": i + 1,
            "track_id": track["id"],
            "track_name": track["name"],
            "artist": ", ".join(a["name"] for a in track["artists"]),
            "album": track["album"]["name"],
            "release_date": track["album"]["release_date"],
            "popularity": track["popularity"],
            "fetched_at": pd.Timestamp.now(),
        })

    # batch audio features (same logic as before)
    ids = [r["track_id"] for r in rows]
    features_by_id = {}
    for start in range(0, len(ids), 100):
        for feat in sp.audio_features(ids[start:start + 100]) or []:
            if feat:
                features_by_id[feat["id"]] = feat

    for r in rows:
        f = features_by_id.get(r["track_id"])
        if f:
            r.update({
                "danceability": f["danceability"],
                "energy": f["energy"],
                "tempo": f["tempo"],
                "valence": f["valence"],
                "loudness": f["loudness"],
                "acousticness": f["acousticness"],
            })
    return pd.DataFrame(rows)


# -------------------------------------------------------
# 2. TOP ARTISTS
# -------------------------------------------------------
def extract_top_artists(sp, time_range="medium_term", limit=50):
    results = sp.current_user_top_artists(time_range=time_range, limit=limit)
    rows = []
    for i, item in enumerate(results["items"]):
        rows.append({
            "rank": i + 1,
            "artist_id": item["id"],
            "artist_name": item["name"],
            "genres": item["genres"],                # list — unnest later
            "popularity": item["popularity"],
            "followers": item["followers"]["total"],
            "time_range": time_range,
            "fetched_at": pd.Timestamp.now(),
        })
    return pd.DataFrame(rows)


# -------------------------------------------------------
# 3. RECENTLY PLAYED (for time-series listening analysis)
# -------------------------------------------------------
def extract_recently_played(sp, limit=50):
    results = sp.current_user_recently_played(limit=limit)
    rows = []
    for item in results["items"]:
        track = item["track"]
        rows.append({
            "played_at": item["played_at"],          # ISO timestamp — your time axis
            "track_id": track["id"],
            "track_name": track["name"],
            "artist": ", ".join(a["name"] for a in track["artists"]),
            "album": track["album"]["name"],
            "popularity": track["popularity"],
        })

    # batch audio features for these too
    ids = list({r["track_id"] for r in rows})
    features_by_id = {}
    for chunk_start in range(0, len(ids), 100):
        for feat in sp.audio_features(ids[chunk_start:chunk_start + 100]) or []:
            if feat:
                features_by_id[feat["id"]] = feat

    for r in rows:
        f = features_by_id.get(r["track_id"])
        if f:
            r.update({
                "danceability": f["danceability"],
                "energy": f["energy"],
                "tempo": f["tempo"],
                "valence": f["valence"],
            })
        r["fetched_at"] = pd.Timestamp.now()

    return pd.DataFrame(rows)


# -------------------------------------------------------
# Quick test — run this file directly to check auth works
# -------------------------------------------------------
if __name__ == "__main__":
    df = pd.read_csv("spotify_tracks.csv")
    print(df.columns.tolist())
    print(df.head())
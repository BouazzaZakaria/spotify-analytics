import numpy as np
import pandas as pd

KEY_NAMES = {0: "C", 1: "C♯/D♭", 2: "D", 3: "D♯/E♭", 4: "E", 5: "F",
             6: "F♯/G♭", 7: "G", 8: "G♯/A♭", 9: "A", 10: "A♯/B♭", 11: "B"}


def transform_tracks(df):
    """Clean and enrich the raw Spotify tracks dataframe."""

    # ---------- 1. Structural cleanup ----------
    df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")], errors="ignore")
    df.columns = df.columns.str.strip().str.lower()

    # ---------- 2. Deduplication ----------
    
    df = (df.sort_values("popularity", ascending=False)
            .drop_duplicates(subset="track_id", keep="first")
            .reset_index(drop=True))
    # ---------- 3. Handle nulls ----------
    audio_cols = ["danceability", "energy", "valence", "tempo", "loudness",
                  "acousticness", "speechiness", "instrumentalness", "liveness"]
    n_before = len(df)
    df = df.dropna(subset=["track_id", "track_name", "tempo"])   # unfixable rows
    for col in audio_cols:
        df[col] = df[col].fillna(df[col].median())               # neutral imputation
    print(f"Dropped {n_before - len(df)} rows with critical nulls")

    # ---------- 4. Derive analyst metrics ----------
    df["mood_score"] = (0.5 * df["valence"] + 0.5 * df["energy"]).round(2)
    df["duration_min"] = (df["duration_ms"] / 60000).round(2)

    # Popularity tiers — business-friendly buckets for the dashboard
    df["popularity_tier"] = pd.cut(df["popularity"],
                                   bins=[-1, 20, 50, 80, 100],
                                   labels=["Niche (<20)", "Mid (20-50)",
                                           "Popular (50-80)", "Hit (80-100)"])

    # Human-readable key/mode instead of integers
    df["key_name"] = df["key"].map(KEY_NAMES).fillna("Unknown")
    df["mode_name"] = df["mode"].map({0: "Minor", 1: "Major"})

    # Energy/Valence quadrant — great for the scatter plot story
    conditions = [
        (df["energy"] >= 0.5) & (df["valence"] >= 0.5),
        (df["energy"] >= 0.5) & (df["valence"] < 0.5),
        (df["energy"] < 0.5) & (df["valence"] >= 0.5),
        (df["energy"] < 0.5) & (df["valence"] < 0.5),
    ]
    df["mood_quadrant"] = np.select(
        conditions,
        ["Energetic & Happy", "Intense & Melancholic", "Chill & Happy", "Chill & Sad"],
        default="Unknown",
    )

    # ---------- 5. Rounding ----------
    df["tempo"] = df["tempo"].round(1)
    df["loudness"] = df["loudness"].round(2)

    # ---------- 6. Genre standardization ----------
    df["track_genre"] = (df["track_genre"].str.lower().str.strip())
    df = df[df["track_genre"].notna()]

    df["loaded_at"] = pd.Timestamp.now()
    return df


def make_artist_bridge(df):
    """One row per track-artist pair for Power BI (avoids split on ';')."""
    bridge = (df[["track_id", "artists"]]
              .assign(artist=lambda d: d["artists"].str.split(";"))
              .explode("artist"))
    bridge["artist"] = bridge["artist"].str.strip()
    return bridge[["track_id", "artist"]].drop_duplicates()


def make_genre_summary(df):
    """Genre-level aggregates — feeds the genre comparison visuals."""
    return (df.groupby("track_genre")
              .agg(track_count=("track_id", "count"),
                   avg_popularity=("popularity", "mean"),
                   avg_energy=("energy", "mean"),
                   avg_valence=("valence", "mean"),
                   avg_danceability=("danceability", "mean"))
              .round(3)
              .reset_index())


if __name__ == "__main__":
    df = pd.read_csv("spotify_tracks.csv")          # your downloaded file
    df = transform_tracks(df)
    print(df.shape)
    print(df[["track_name", "track_genre", "popularity_tier", "mood_score"]].head())

    make_artist_bridge(df).to_csv("artist_bridge.csv", index=False)
    make_genre_summary(df).to_csv("genre_summary.csv", index=False)
    print("\n✅ transform complete — bridge + summary tables saved")
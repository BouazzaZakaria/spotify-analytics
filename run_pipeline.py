import pandas as pd
from transform import transform_tracks, make_artist_bridge, make_genre_summary
from load import load

df = pd.read_csv("spotify_tracks.csv")
df = transform_tracks(df)

load(df, "tracks_clean")
load(make_artist_bridge(df), "artist_bridge")
load(make_genre_summary(df), "genre_summary")

print("Pipeline complete ✅")
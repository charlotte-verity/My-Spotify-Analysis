import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import plotly.express as px

streaming_pre = './streaming_history_files'
streaming_paths = os.listdir(streaming_pre)
audio_paths = [x for x in streaming_paths if "Audio" in x]
audio_2025_paths = [x for x in audio_paths if "2025" in x]

# Takes in list of data file paths of streaming data jsons and date limits
def load_streaming_files(paths, min_date = None, max_date = None):
  streaming_data = pd.DataFrame()
  for p in sorted(paths):
    df_temp = pd.read_json(streaming_pre+"/"+p)
    df_temp["stream_date"] = pd.to_datetime(df_temp["ts"]).dt.date
    df_temp["ts"] = pd.to_datetime(df_temp["ts"])
    streaming_data = pd.concat([streaming_data, df_temp])
  if(min_date is not None):
    streaming_data = streaming_data[(streaming_data["stream_date"]>=pd.to_datetime(min_date).date())]
  if(max_date is not None):
    streaming_data = streaming_data[(streaming_data["stream_date"]<=pd.to_datetime(max_date).date())]
  streaming_data = streaming_data[~streaming_data["master_metadata_track_name"].isna()]
  return streaming_data

# Keep necessary, non-PI columns
def clean_streaming_data(streaming_data):
  streaming_data = streaming_data[['platform', 'ms_played', 'master_metadata_track_name', 'master_metadata_album_artist_name', 
                               'master_metadata_album_album_name', 'spotify_track_uri', 'reason_start', 'reason_end', 
                               'skipped', 'stream_date', 'ts']].copy()
  streaming_data["seconds"] = streaming_data["ms_played"]/1000
  streaming_data["minutes"] = streaming_data["seconds"]/60
  return streaming_data

def get_summary_stats(streaming_data):
  minutes_played = streaming_data["minutes"].sum()
  songs_played = streaming_data["spotify_track_uri"].count()
  unique_songs_played = streaming_data.groupby(["master_metadata_track_name", "master_metadata_album_artist_name"]).ngroups
  artists_played = streaming_data["master_metadata_album_artist_name"].nunique()
  print("Total minutes played: "+str(minutes_played))
  print("Total songs played: "+str(songs_played))
  print("Unique songs played: "+str(unique_songs_played))
  print("Unique artists played: "+str(artists_played))

def get_most_played_songs(streaming_data):
  most_played_songs = streaming_data.groupby(["master_metadata_track_name", "master_metadata_album_artist_name"])["master_metadata_track_name"]\
                                    .count().reset_index(name="plays").sort_values("plays", ascending=False)
  print("Most played songs: ")
  display(most_played_songs.head(5))
  return most_played_songs

def get_longest_played_songs(streaming_data):
  longest_played_songs = streaming_data.groupby(["master_metadata_track_name", "master_metadata_album_artist_name"])["minutes"]\
                         .sum().reset_index(name="minutes").sort_values("minutes", ascending=False)
  print("Longest played songs: ")
  display(longest_played_songs.head(5))
  return longest_played_songs

def get_most_played_artists(streaming_data):
  most_played_artists = streaming_data.groupby(["master_metadata_album_artist_name"])["master_metadata_track_name"]\
                         .count().reset_index(name="plays").sort_values("plays", ascending=False)
  print("Most played artists: ")
  display(most_played_artists.head(5))
  return most_played_artists

def get_longest_played_artists(streaming_data):
  longest_played_artists = streaming_data.groupby(["master_metadata_album_artist_name"])["minutes"]\
                          .sum().reset_index(name="minutes").sort_values("minutes", ascending=False)
  print("Longest played artists: ")
  display(longest_played_artists.head(5))
  return longest_played_artists

audio_2025_df = load_streaming_files(audio_2025_paths, "2025-01-01", "2025-12-31")
audio_2025_df = clean_streaming_data(audio_2025_df)
print(audio_2025_df["stream_date"].min())
print(audio_2025_df["stream_date"].max())
print(audio_2025_df.shape)
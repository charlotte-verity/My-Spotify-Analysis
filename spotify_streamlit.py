import numpy as np
import pandas as pd
import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import Counter

# Page config
st.set_page_config(
    page_title="2025 Spotify Dashboard",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Data loading functions
streaming_pre = './streaming_history_files'

@st.cache_data
def load_streaming_files(paths, min_date=None, max_date=None):
    """Load and combine streaming history files"""
    streaming_data = pd.DataFrame()
    for p in sorted(paths):
        df_temp = pd.read_json(streaming_pre + "/" + p)
        df_temp["stream_date"] = pd.to_datetime(df_temp["ts"]).dt.date
        df_temp["ts"] = pd.to_datetime(df_temp["ts"])
        streaming_data = pd.concat([streaming_data, df_temp])
    
    if min_date is not None:
        streaming_data = streaming_data[(streaming_data["stream_date"] >= pd.to_datetime(min_date).date())]
    if max_date is not None:
        streaming_data = streaming_data[(streaming_data["stream_date"] <= pd.to_datetime(max_date).date())]
    
    streaming_data = streaming_data[~streaming_data["master_metadata_track_name"].isna()]
    return streaming_data

@st.cache_data
def clean_streaming_data(streaming_data):
    """Keep necessary, non-PI columns"""
    streaming_data = streaming_data[['platform', 'ms_played', 'master_metadata_track_name', 
                                      'master_metadata_album_artist_name', 'master_metadata_album_album_name', 
                                      'spotify_track_uri', 'reason_start', 'reason_end', 'skipped', 
                                      'stream_date', 'ts']].copy()
    streaming_data["seconds"] = streaming_data["ms_played"] / 1000
    streaming_data["minutes"] = streaming_data["seconds"] / 60
    return streaming_data

# Load data
streaming_paths = os.listdir(streaming_pre)
audio_paths = [x for x in streaming_paths if "Audio" in x]
audio_2025_paths = [x for x in audio_paths if "2025" in x]

audio_2025_df = load_streaming_files(audio_2025_paths, "2025-01-01", "2025-12-31")
audio_2025_df = clean_streaming_data(audio_2025_df)

# Dashboard title
st.title("🎵 2025 Spotify Streaming Dashboard")
st.markdown("Your personalized Spotify listening analytics for 2025")

# Key Metrics
col1, col2, col3, col4 = st.columns(4)

total_minutes = audio_2025_df["minutes"].sum()
total_songs = audio_2025_df["spotify_track_uri"].count()
unique_songs = audio_2025_df.groupby(["master_metadata_track_name", "master_metadata_album_artist_name"]).ngroups
unique_artists = audio_2025_df["master_metadata_album_artist_name"].nunique()

col1.metric("Total Minutes Played", f"{total_minutes:,.0f}")
col2.metric("Total Streams", f"{total_songs:,}")
col3.metric("Unique Songs", f"{unique_songs:,}")
col4.metric("Unique Artists", f"{unique_artists:,}")

st.divider()

# Tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🎤 Artists", "🎵 Songs", "📅 Timeline", "📱 Platform"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Hours per day average
        streams_per_day = audio_2025_df.groupby("stream_date")["minutes"].sum().reset_index()
        avg_minutes_per_day = streams_per_day["minutes"].mean()
        st.metric("Average Minutes/Day", f"{avg_minutes_per_day:.1f}")
        
        # Listening hours per day chart
        fig_daily = px.bar(streams_per_day, x="stream_date", y="minutes",
                           title="Daily Listening Minutes",
                           labels={"stream_date": "Date", "minutes": "Minutes"},
                           color="minutes",
                           color_continuous_scale="viridis")
        fig_daily.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_daily, use_container_width=True)
    
    with col2:
        # Skipped vs completed
        skip_stats = audio_2025_df["skipped"].value_counts()
        fig_skip = px.pie(values=skip_stats.values, names=['Completed', 'Skipped'],
                         title="Completed vs Skipped Streams",
                         color_discrete_map={0: '#1DB954', 1: '#191414'})
        fig_skip.update_layout(height=400)
        st.plotly_chart(fig_skip, use_container_width=True)
    
    # Platform distribution
    platform_counts = audio_2025_df["platform"].value_counts()
    fig_platform = px.pie(values=platform_counts.values, names=platform_counts.index,
                         title="Listening by Platform",
                         color_discrete_sequence=px.colors.qualitative.Set2)
    fig_platform.update_layout(height=400)
    st.plotly_chart(fig_platform, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Artists by Plays")
        top_artists_plays = audio_2025_df.groupby("master_metadata_album_artist_name")["master_metadata_track_name"]\
                            .count().reset_index(name="plays").sort_values("plays", ascending=False).head(15)
        
        fig_artists_plays = px.bar(top_artists_plays, x="plays", y="master_metadata_album_artist_name",
                                   orientation="h",
                                   labels={"master_metadata_album_artist_name": "Artist", "plays": "Number of Plays"},
                                   color="plays",
                                   color_continuous_scale="blues")
        fig_artists_plays.update_layout(yaxis_categoryorder="total ascending", height=500)
        st.plotly_chart(fig_artists_plays, use_container_width=True)
    
    with col2:
        st.subheader("Top Artists by Minutes Played")
        top_artists_minutes = audio_2025_df.groupby("master_metadata_album_artist_name")["minutes"]\
                              .sum().reset_index(name="minutes").sort_values("minutes", ascending=False).head(15)
        
        fig_artists_minutes = px.bar(top_artists_minutes, x="minutes", y="master_metadata_album_artist_name",
                                     orientation="h",
                                     labels={"master_metadata_album_artist_name": "Artist", "minutes": "Minutes"},
                                     color="minutes",
                                     color_continuous_scale="greens")
        fig_artists_minutes.update_layout(yaxis_categoryorder="total ascending", height=500)
        st.plotly_chart(fig_artists_minutes, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Songs by Plays")
        top_songs_plays = audio_2025_df.groupby(["master_metadata_track_name", "master_metadata_album_artist_name"])\
                          ["master_metadata_track_name"].count().reset_index(name="plays")\
                          .sort_values("plays", ascending=False).head(15)
        top_songs_plays["song"] = top_songs_plays["master_metadata_track_name"] + " - " + top_songs_plays["master_metadata_album_artist_name"]
        
        fig_songs_plays = px.bar(top_songs_plays, x="plays", y="song",
                                orientation="h",
                                labels={"plays": "Number of Plays", "song": ""},
                                color="plays",
                                color_continuous_scale="purples")
        fig_songs_plays.update_layout(yaxis_categoryorder="total ascending", height=500)
        st.plotly_chart(fig_songs_plays, use_container_width=True)
    
    with col2:
        st.subheader("Top Songs by Minutes Played")
        top_songs_minutes = audio_2025_df.groupby(["master_metadata_track_name", "master_metadata_album_artist_name"])\
                            ["minutes"].sum().reset_index(name="minutes")\
                            .sort_values("minutes", ascending=False).head(15)
        top_songs_minutes["song"] = top_songs_minutes["master_metadata_track_name"] + " - " + top_songs_minutes["master_metadata_album_artist_name"]
        
        fig_songs_minutes = px.bar(top_songs_minutes, x="minutes", y="song",
                                  orientation="h",
                                  labels={"minutes": "Minutes", "song": ""},
                                  color="minutes",
                                  color_continuous_scale="oranges")
        fig_songs_minutes.update_layout(yaxis_categoryorder="total ascending", height=500)
        st.plotly_chart(fig_songs_minutes, use_container_width=True)

with tab4:
    col1, col2 = st.columns(2)
    
    with col1:
        # Monthly trends
        audio_2025_df["year_month"] = pd.to_datetime(audio_2025_df["stream_date"]).dt.to_period("M")
        monthly_stats = audio_2025_df.groupby("year_month").agg({
            "minutes": "sum",
            "spotify_track_uri": "count"
        }).reset_index()
        monthly_stats.columns = ["Month", "minutes", "plays"]
        monthly_stats["Month"] = monthly_stats["Month"].astype(str)
        
        fig_monthly = px.line(monthly_stats, x="Month", y="minutes",
                             title="Monthly Listening Minutes",
                             markers=True,
                             labels={"minutes": "Minutes", "Month": "Month"})
        fig_monthly.update_layout(height=400)
        st.plotly_chart(fig_monthly, use_container_width=True)
    
    with col2:
        # Day of week analysis
        audio_2025_df["day_of_week"] = pd.to_datetime(audio_2025_df["stream_date"]).dt.day_name()
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dow_stats = audio_2025_df.groupby("day_of_week")["minutes"].sum().reindex(day_order).reset_index()
        
        fig_dow = px.bar(dow_stats, x="day_of_week", y="minutes",
                        title="Listening by Day of Week",
                        labels={"day_of_week": "Day", "minutes": "Minutes"},
                        color="minutes",
                        color_continuous_scale="teal")
        fig_dow.update_layout(height=400)
        st.plotly_chart(fig_dow, use_container_width=True)
    
    # Hour of day analysis
    audio_2025_df["hour"] = pd.to_datetime(audio_2025_df["ts"]).dt.hour
    hourly_stats = audio_2025_df.groupby("hour")["minutes"].sum().reset_index()
    
    fig_hourly = px.bar(hourly_stats, x="hour", y="minutes",
                       title="Listening by Hour of Day",
                       labels={"hour": "Hour of Day", "minutes": "Minutes"},
                       color="minutes",
                       color_continuous_scale="sunset")
    fig_hourly.update_layout(height=400)
    st.plotly_chart(fig_hourly, use_container_width=True)

with tab5:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Platform Distribution")
        platform_stats = audio_2025_df.groupby("platform").agg({
            "minutes": "sum",
            "spotify_track_uri": "count"
        }).reset_index()
        platform_stats.columns = ["Platform", "minutes", "plays"]
        
        fig_platform_detail = px.bar(platform_stats, x="Platform", y="minutes",
                                    title="Total Minutes by Platform",
                                    labels={"minutes": "Minutes"},
                                    color="minutes",
                                    color_continuous_scale="viridis")
        st.plotly_chart(fig_platform_detail, use_container_width=True)
    
    with col2:
        st.subheader("Platform Plays")
        fig_platform_plays = px.bar(platform_stats, x="Platform", y="plays",
                                   title="Total Streams by Platform",
                                   labels={"plays": "Number of Plays"},
                                   color="plays",
                                   color_continuous_scale="plasma")
        st.plotly_chart(fig_platform_plays, use_container_width=True)
    
    # Platform details table
    st.dataframe(platform_stats.sort_values("minutes", ascending=False), use_container_width=True)
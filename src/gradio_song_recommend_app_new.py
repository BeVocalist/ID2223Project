import gradio as gr
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import hopsworks
import pandas as pd
import os

load_dotenv()

# 初始化 Spotify 客户端
def init_spotify_client():
    return Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="user-top-read"
    ))

# 获取用户的 Top Tracks
def fetch_top_tracks(spotify_client, limit=10, time_range="short_term"):
    results = spotify_client.current_user_top_tracks(limit=limit, time_range=time_range)
    return results["items"]

# Gradio 推理函数
def process_user_data():
    log = ""  # 累积日志
    try:
        log += "Step 1: Initializing Spotify client...\n"
        yield log
        spotify_client = init_spotify_client()

        log += "Step 2: Fetching user's top tracks from Spotify...\n"
        yield log
        top_tracks = fetch_top_tracks(spotify_client, limit=10, time_range="short_term")

        log += "Top 10 songs user played most recently:\n"
        for i, track in enumerate(top_tracks, 1):
            track_id = track["id"]
            track_name = track["name"]
            artists = ", ".join(artist["name"] for artist in track["artists"])
            popularity = track["popularity"]

            log += f"{i}. Track ID: {track_id}\n"
            log += f"   Track Name: {track_name}\n"
            log += f"   Artist Name: {artists}\n"
            log += f"   Popularity: {popularity}\n"
            log += "-" * 50 + "\n"
        yield log

        log += "Step 3: Processing data into a DataFrame...\n"
        yield log
        extra_fields = {
            "album_name": "unknown_album",
            "duration_ms": 0,
            "acousticness": 0,
            "danceability": 0,
            "energy": 0,
            "key": 0,
            "loudness": 0,
            "mode": 0,
            "speechiness": 0,
            "instrumentalness": 0,
            "liveness": 0,
            "tempo": 0,
            "time_signature": 0,
            "artist_avg_popularity": 0,
            "artist_popularity_std": 0,
            "artist_track_count": 0,
            "artist_avg_acousticness": 0,
            "artist_avg_danceability": 0,
            "artist_avg_energy": 0,
            "duration_minutes": 0
        }

        data = []
        for track in top_tracks:
            normalized_popularity = track["popularity"] / 100.0
            row = {
                "track_id": track["id"],
                "track_name": track["name"],
                "artist_name": ", ".join(artist["name"] for artist in track["artists"]),
                "popularity": normalized_popularity
            }
            row.update(extra_fields)
            data.append(row)

        df = pd.DataFrame(data)
        log += f"DataFrame:\n{df.to_string(index=False)}\n"
        yield log

        log += "Step 4: Saving data to output.csv...\n"
        yield log
        df.to_csv("output.csv", index=False)
        log += "Data saved to output.csv\n"
        yield log

        log += "Step 5: Connecting to Hopsworks...\n"
        yield log
        os.environ["HOPSWORKS_API_KEY"] = os.getenv("HOPSWORKS_API_KEY")
        project = hopsworks.login()
        fs = project.get_feature_store()

        log += f"Project Name: {project.name}\n"
        yield log

        feature_group = fs.get_feature_group(name="spotify_features", version=2)
        log += f"Selected Feature Group: {feature_group}\n"
        yield log

        log += "Step 6: Uploading data to Hopsworks...\n"
        yield log
        columns_to_convert = [
            "acousticness", "danceability", "energy", "loudness", "speechiness", 
            "instrumentalness", "liveness", "tempo", "time_signature", 
            "artist_avg_popularity", "artist_popularity_std", "artist_track_count", 
            "artist_avg_acousticness", "artist_avg_danceability", "artist_avg_energy", 
            "duration_minutes"
        ]
        df[columns_to_convert] = df[columns_to_convert].astype(float)
        feature_group.insert(df, write_options={"wait_for_job": True})

        log += "Data uploaded to Hopsworks successfully!\n"
        yield log

    except Exception as e:
        log += f"Error: {str(e)}\n"
        yield log

# Gradio 界面
with gr.Blocks() as app:
    gr.Markdown("# Spotify Data Upload to Hopsworks")
    fetch_button = gr.Button("Fetch and Upload Spotify Data")
    output = gr.Textbox(label="Execution Progress", lines=15)
    fetch_button.click(fn=process_user_data, inputs=[], outputs=output)

# 启动 Gradio 应用
app.launch()

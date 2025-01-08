from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import hopsworks
import pandas as pd
import os

load_dotenv()

# def init_spotify_client():
#     """Initialize the Spotify client."""
#     return Spotify(auth_manager=SpotifyOAuth(
#         client_id=os.getenv("SPOTIPY_CLIENT_ID"),
#         client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
#         redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
#         scope="user-top-read"
#     ))

def generate_access_token():
    """Generate Spotify access token."""
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="user-top-read"
    )
    token_info = auth_manager.get_access_token(as_dict=True)
    return token_info["access_token"]

def init_spotify_client():
    """Initialize Spotify client with a valid access token."""
    # 如果未配置 SPOTIFY_ACCESS_TOKEN，动态生成
    access_token = os.getenv("SPOTIFY_ACCESS_TOKEN")
    if not access_token:
        print("Generating a new access token...")
        access_token = generate_access_token()
    return Spotify(auth=access_token)

def fetch_top_tracks(spotify_client, limit=10, time_range="short_term"):
    """Fetch user's top tracks."""
    results = spotify_client.current_user_top_tracks(limit=limit, time_range=time_range)
    return results["items"]

def process_spotify_data(tracks):
    """Process Spotify data and return a DataFrame."""
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
    for track in tracks:
        normalized_popularity = track["popularity"] / 100.0
        row = {
            "track_id": track["id"],
            "track_name": track["name"],
            "artist_name": ", ".join(artist["name"] for artist in track["artists"]),
            "popularity": normalized_popularity
        }
        row.update(extra_fields)
        data.append(row)

    return pd.DataFrame(data)

def upload_to_hopsworks(df, feature_group_name="spotify_features", version=2):
    """Upload DataFrame to Hopsworks Feature Group."""
    os.environ["HOPSWORKS_API_KEY"] = "K86PR55oWoqOXhUX.VUJFWq1zEqfhZntoebWp1RLsH90VVbAYuqukvh5AcM8xHOYk7c4vg4VvD6iZEG37"
    project = hopsworks.login()
    fs = project.get_feature_store()
    feature_group = fs.get_feature_group(name=feature_group_name, version=version)

    # 转换列为 float 类型
    columns_to_convert = [
        "acousticness", "danceability", "energy", "loudness", "speechiness", 
        "instrumentalness", "liveness", "tempo", "time_signature", 
        "artist_avg_popularity", "artist_popularity_std", "artist_track_count", 
        "artist_avg_acousticness", "artist_avg_danceability", "artist_avg_energy", 
        "duration_minutes"
    ]
    df[columns_to_convert] = df[columns_to_convert].astype(float)

    # 上传数据
    feature_group.insert(df, write_options={"wait_for_job": True})
    return "Data uploaded to Hopsworks successfully!"

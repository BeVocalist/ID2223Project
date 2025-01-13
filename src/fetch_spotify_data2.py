from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import hopsworks
import pandas as pd
import os

load_dotenv()


def init_spotify_client():
    return Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="user-top-read"
    ))


def fetch_top_tracks(spotify_client, limit=10, time_range="short_term"):
    
    results = spotify_client.current_user_top_tracks(limit=limit, time_range=time_range)
    return results["items"]


if __name__ == "__main__":
    
    spotify_client = init_spotify_client()

    
    top_tracks = fetch_top_tracks(spotify_client, limit=10, time_range="short_term")

    

    # print("Top 10 songs user played most recently:")
    # for i, track in enumerate(top_tracks, 1):
    #     track_id = track["id"]  
    #     track_name = track["name"]  
    #     artists = ", ".join(artist["name"] for artist in track["artists"]) 
    #     popularity = track["popularity"] 

        
    #     print(f"{i}.track_id: {track_id}")
    #     print(f" track_name: {track_name}")
    #     print(f" artist_name: {artists}")
    #     print(f" popularity: {popularity}")
    #     print("-" * 50)

    print("Top 10 songs user played most recently:")
    # 欄位名稱與初始值設置
    extra_fields = {
        "album_name": "unknown_album",  # 可以用 "unknown" 或其他佔位符填充
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
    print(df.to_string())
    df.to_csv("output.csv", index=True)
    print("Data saved to output.csv")

    os.environ["HOPSWORKS_API_KEY"] = "K86PR55oWoqOXhUX.VUJFWq1zEqfhZntoebWp1RLsH90VVbAYuqukvh5AcM8xHOYk7c4vg4VvD6iZEG37"
    project = hopsworks.login()
    fs = project.get_feature_store()
    print("project.name:")
    print(project.name)


    
    feature_group = fs.get_feature_group(name="spotify_features", version=2)
    print("Selected Feature Group:")
    print(feature_group)

    columns_to_convert = [
        "acousticness", "danceability", "energy", "loudness", "speechiness", 
        "instrumentalness", "liveness", "tempo", "time_signature", 
        "artist_avg_popularity", "artist_popularity_std", "artist_track_count", 
        "artist_avg_acousticness", "artist_avg_danceability", "artist_avg_energy", 
        "duration_minutes"
    ]

    df[columns_to_convert] = df[columns_to_convert].astype(float)

    print("Data types after conversion:")
    # print(df.dtypes)




    feature_group.insert(df, write_options={"wait_for_job": True})
    print("Data uploaded to Hopsworks successfully!")






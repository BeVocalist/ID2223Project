from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
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

    

    print("Top 10 songs user played most recently")
    for i, track in enumerate(top_tracks, 1):
        track_name = track["name"]
        artists = ", ".join(artist["name"] for artist in track["artists"])
        album_name = track["album"]["name"]
        album_release_date = track["album"]["release_date"]
        track_duration_ms = track["duration_ms"]
        popularity = track["popularity"]
        preview_url = track["preview_url"]

        
        track_duration_min = track_duration_ms / 60000

        print(f"{i}. {track_name} by {artists}")
        print(f"   Album: {album_name} (Released: {album_release_date})")
        print(f"   Duration: {track_duration_min:.2f} minutes")
        print(f"   Popularity: {popularity}")
        print(f"   Preview URL: {preview_url}")
        print("-" * 50)

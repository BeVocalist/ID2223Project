from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

load_dotenv()

def generate_access_token():
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="user-top-read"
    )
    token_info = auth_manager.get_access_token(as_dict=True)
    print("Access Token:", token_info["access_token"])
    return token_info["access_token"]

if __name__ == "__main__":
    generate_access_token()

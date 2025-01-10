import gradio as gr
from fetch_spotify_data_module import (
    init_spotify_client, 
    fetch_top_tracks, 
    process_spotify_data,
    upload_to_hopsworks,
    create_recommendation_playlist
)
from recommendation_module import get_recommendations

class AppState:
    def __init__(self):
        self.spotify_client = None
        self.recommendations = None

app_state = AppState()

def process_user_data():
    log = ""
    try:
        log += "🎵 Step 1: Initializing Spotify client...\n"
        yield log
        app_state.spotify_client = init_spotify_client()

        log += "📊 Step 2: Fetching your top tracks from Spotify...\n"
        yield log
        top_tracks = fetch_top_tracks(app_state.spotify_client, limit=10, time_range="short_term")

        log += "\n🎧 Your Top 10 Recent Tracks:\n"
        log += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, track in enumerate(top_tracks, 1):
            track_name = track["name"]
            artists = ", ".join(artist["name"] for artist in track["artists"])
            log += f"{i}. 🎵 {track_name}\n   👤 {artists}\n"
        log += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        yield log

        log += "\n📝 Step 3: Processing data...\n"
        yield log
        df = process_spotify_data(top_tracks)

        log += "💾 Step 4: Uploading data to Hopsworks...\n"
        yield log
        result = upload_to_hopsworks(df)
        log += f"✅ {result}\n"
        yield log

        log += "🎯 Step 5: Getting personalized recommendations...\n"
        yield log
        app_state.recommendations = get_recommendations(top_tracks)
        log += "\n🌟 Recommended Songs:\n"
        log += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, (_, row) in enumerate(app_state.recommendations.iterrows(), 1):
            log += f"{i}. 🎵 {row['track_name']}\n   👤 {row['artist_name']}\n"
        log += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        log += "\n✨ Click 'Create Playlist' to save these recommendations to your Spotify account!\n"
        yield log

    except Exception as e:
        log += f"\n❌ Error: {str(e)}\n"
        yield log

def create_playlist():
    if app_state.spotify_client is None or app_state.recommendations is None:
        return "⚠️ Please fetch recommendations first!", ""
    
    try:
        result = create_recommendation_playlist(app_state.spotify_client, app_state.recommendations)
        if result['url']:
            html_link = f'''
            <div style="text-align: center; padding: 10px;">
                <a href="{result["url"]}" target="_blank" style="
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #1DB954;
                    color: white;
                    text-decoration: none;
                    border-radius: 20px;
                    font-weight: bold;
                    transition: all 0.3s ease;">
                    🎧 Open in Spotify
                </a>
            </div>
            '''
            return f"✅ Success! {result['message']}", html_link
        return f"✅ Success! {result['message']}", ""
    except Exception as e:
        return f"❌ Error creating playlist: {str(e)}", ""

with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown(
        """
        # 🎵 Spotify Music Recommendation System
        Get personalized music recommendations based on your listening history!
        """
    )
    
    with gr.Group():
        with gr.Row():
            with gr.Column(scale=1):
                fetch_button = gr.Button("🔍 Analyze My Music", variant="primary", size="lg")
                create_playlist_button = gr.Button("💫 Create Playlist", variant="secondary", size="lg")
            
        with gr.Column(scale=2):
            output = gr.Textbox(
                label="Progress & Results", 
                lines=15,
                show_label=False,
                container=True
            )
            playlist_link = gr.HTML(label="Playlist Link")

    gr.Markdown(
        """
        ### 📝 How it works:
        1. Click "Analyze My Music" to scan your recent listening history
        2. Wait for personalized recommendations based on your taste
        3. Click "Create Playlist" to save recommendations to your Spotify account
        """
    )

    fetch_button.click(fn=process_user_data, inputs=[], outputs=output)
    create_playlist_button.click(
        fn=create_playlist, 
        inputs=[], 
        outputs=[output, playlist_link]
    )


if __name__ == "__main__":
    app.launch()

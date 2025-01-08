import gradio as gr
from fetch_spotify_data_module import init_spotify_client, fetch_top_tracks, process_spotify_data, upload_to_hopsworks

# Gradio 推理函数带进度累积
def process_user_data():
    log = ""  # 累积日志

    try:
        log += "Step 1: Initializing Spotify client...\n"
        yield log
        # 初始化 Spotify 客户端
        spotify_client = init_spotify_client()

        log += "Step 2: Fetching user's top tracks from Spotify...\n"
        yield log
        # 获取用户 Spotify 数据
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

        log += "Step 3: Processing fetched data into a DataFrame...\n"
        yield log
        # 处理数据
        df = process_spotify_data(top_tracks)

        log += f"Step 4: Data processed successfully! DataFrame preview:\n{df[['track_name', 'artist_name']].to_string(index=False)}\n"
        yield log

    except Exception as e:
        log += f"Error during data fetching or processing: {str(e)}\n"
        yield log
        return

    try:
        log += "Step 5: Uploading data to Hopsworks Feature Group...\n"
        yield log
        # 上传数据到 Hopsworks
        result = upload_to_hopsworks(df)

        log += f"Step 6: Data uploaded successfully to Hopsworks! Result:\n{result}\n"
        yield log

    except Exception as e:
        log += f"Error during data upload to Hopsworks: {str(e)}\n"
        yield log
        return

# Gradio 界面
with gr.Blocks() as app:
    gr.Markdown("# Spotify Data Upload to Hopsworks")
    fetch_button = gr.Button("Fetch and Upload Spotify Data")
    output = gr.Textbox(label="Execution Progress", lines=15)
    # output = gr.Markdown(label="Execution Progress")

    fetch_button.click(fn=process_user_data, inputs=[], outputs=output)

# 启动 Gradio 应用
app.launch()

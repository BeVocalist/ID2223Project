import gradio as gr
from fetch_spotify_data_module import init_spotify_client, fetch_top_tracks, process_spotify_data, upload_to_hopsworks

# Gradio 推理函数带进度
def process_user_data():
    try:
        yield "Step 1: Initializing Spotify client..."
        # 初始化 Spotify 客户端
        spotify_client = init_spotify_client()

        yield "Step 2: Fetching user's top tracks from Spotify..."
        # 获取用户 Spotify 数据
        top_tracks = fetch_top_tracks(spotify_client, limit=10, time_range="short_term")

        yield "Step 3: Processing fetched data into a DataFrame..."
        # 处理数据
        df = process_spotify_data(top_tracks)

        yield f"Step 4: Data processed successfully! Preview:\n{df[['track_name', 'artist_name']].to_string(index=False)}"
    except Exception as e:
        yield f"Error during data fetching or processing: {str(e)}"
        return

    try:
        yield "Step 5: Uploading data to Hopsworks Feature Group..."
        # 上传数据到 Hopsworks
        result = upload_to_hopsworks(df)

        yield f"Step 6: Data uploaded successfully to Hopsworks! Result:\n{result}"
    except Exception as e:
        yield f"Error during data upload to Hopsworks: {str(e)}"

# Gradio 界面
with gr.Blocks() as app:
    gr.Markdown("# Spotify Data Upload to Hopsworks")
    fetch_button = gr.Button("Fetch and Upload Spotify Data")
    output = gr.Textbox(label="Execution Progress", lines=10)
    fetch_button.click(fn=process_user_data, inputs=[], outputs=output)

# 启动 Gradio 应用
app.launch()

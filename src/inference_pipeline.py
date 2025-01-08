import os
import joblib
import hopsworks

def load_model():
    """
    Load the trained model and encoders from local files or Hopsworks
    """
    model_dir = "./knn_model"
    
    try:
        # Load local model and encoders
        knn_model = joblib.load(os.path.join(model_dir, "knn_model.pkl"))
        label_encoder_artist = joblib.load(os.path.join(model_dir, "artist_encoder.pkl"))
        label_encoder_track = joblib.load(os.path.join(model_dir, "track_encoder.pkl"))
        return knn_model, label_encoder_artist, label_encoder_track
    except Exception as e:
        print(f"Failed to load local model: {e}")
        # Attempt to load from Hopsworks if local load fails
        try:
            project = hopsworks.login()
            mr = project.get_model_registry()
            model = mr.get_model("knn_recommendation_model")
            model_dir = model.download()
            
            knn_model = joblib.load(os.path.join(model_dir, "knn_model.pkl"))
            label_encoder_artist = joblib.load(os.path.join(model_dir, "artist_encoder.pkl"))
            label_encoder_track = joblib.load(os.path.join(model_dir, "track_encoder.pkl"))
            return knn_model, label_encoder_artist, label_encoder_track
        except Exception as e:
            print(f"Failed to load model from Hopsworks: {e}")
            return None, None, None

def recommend_songs(user_tracks, knn_model, training_data, top_n=10):
    """
    Generate song recommendations based on user's input tracks
    
    Args:
        user_tracks (list): List of track names
        knn_model: Trained KNN model
        training_data (pd.DataFrame): Training data with encoded features
        top_n (int): Number of recommendations to return
    
    Returns:
        pd.DataFrame: Recommended tracks and artists
    """
    training_data = training_data.copy()
    training_data['track_name'] = training_data['track_name'].str.strip().str.lower()
    user_tracks = [track.strip().lower() for track in user_tracks]
    
    filtered_tracks = training_data[training_data['track_name'].isin(user_tracks)]
    if filtered_tracks.empty:
        print("No matching tracks found for user. Using default recommendations.")
        return training_data.sort_values(by='popularity', ascending=False).head(top_n)
    
    user_features = filtered_tracks[['popularity', 'artist_encoded', 'track_encoded']].values
    distances, indices = knn_model.kneighbors(user_features, n_neighbors=top_n)
    
    recommendations = training_data.iloc[indices.flatten()[:top_n]]
    return recommendations[['track_name', 'artist_name']]

def main():
    # Load model and encoders
    knn_model, label_encoder_artist, label_encoder_track = load_model()
    if knn_model is None:
        print("Failed to load model and encoders")
        return
    
    # Example usage
    user_top_tracks = [
        'Comedy', 
        'Hold On',
        'Say Something',
        'Falling in Love at a Coffee Shop',
        'Lucky',
        'Left for America',
        'あ。っという間はあるさ',
        'Pussy Cat',
        'Look For The Good (Single Version)'
    ]
    
    # Get recommendations
    recommended_songs = recommend_songs(user_top_tracks, knn_model, training_data, top_n=5)
    print("\nRecommended songs based on your input:")
    print(recommended_songs)

if __name__ == "__main__":
    main()
import hopsworks
import os
from sklearn.preprocessing import LabelEncoder
import joblib

def get_recommendations(top_tracks):
    """Get song recommendations using the model from Hopsworks based on user's top tracks."""
    try:
        project = hopsworks.login()
        mr = project.get_model_registry()
        model = mr.get_model("knn_recommendation_model")
        model_dir = model.download()
        knn_model = joblib.load(os.path.join(model_dir, "knn_model.pkl"))
        
        # Get feature data
        fs = project.get_feature_store()
        spotify_features = fs.get_feature_group(name="spotify_features", version=2)
        df = spotify_features.read()
        
        # Prepare data
        selected_columns = ['popularity', 'artist_name', 'track_name']
        training_data = df[selected_columns].copy()
        
        # Encode features
        label_encoder_artist = LabelEncoder()
        label_encoder_track = LabelEncoder()
        training_data['artist_encoded'] = label_encoder_artist.fit_transform(training_data['artist_name'])
        training_data['track_encoded'] = label_encoder_track.fit_transform(training_data['track_name'])
        
        # Get recommendations
        training_data = training_data.copy()
        training_data['track_name'] = training_data['track_name'].str.strip().str.lower()
        
        # Extract track names from top_tracks
        user_tracks = [track["name"].strip().lower() for track in top_tracks]
        filtered_tracks = training_data[training_data['track_name'].isin(user_tracks)]
        
        if filtered_tracks.empty:
            return training_data.sort_values(by='popularity', ascending=False).head(10)[['track_name', 'artist_name']]
        
        user_features = filtered_tracks[['popularity', 'artist_encoded', 'track_encoded']].values
        distances, indices = knn_model.kneighbors(user_features, n_neighbors=10)
        recommendations = training_data.iloc[indices.flatten()[:10]]
        
        return recommendations[['track_name', 'artist_name']]
        
    except Exception as e:
        raise Exception(f"Error getting recommendations: {str(e)}")

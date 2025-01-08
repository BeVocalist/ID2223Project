import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.neighbors import NearestNeighbors
import hopsworks
import os
import joblib

def main():
    # Set API key (recommended to use environment variables)
    os.environ["HOPSWORKS_API_KEY"] = "K86PR55oWoqOXhUX.VUJFWq1zEqfhZntoebWp1RLsH90VVbAYuqukvh5AcM8xHOYk7c4vg4VvD6iZEG37"
    
    # Log in to Hopsworks
    try:
        project = hopsworks.login()
    except Exception as e:
        print(f"Failed to login to Hopsworks: {e}")
        return
    
    # Retrieve feature group
    fs = project.get_feature_store()
    try:
        spotify_features = fs.get_feature_group(name="spotify_features", version=2)
        df = spotify_features.read()
    except Exception as e:
        print(f"Failed to retrieve feature group: {e}")
        return
    
    # Select and encode features
    selected_columns = ['popularity', 'artist_name', 'track_name']
    training_data = df[selected_columns].copy()
    
    label_encoder_artist = LabelEncoder()
    label_encoder_track = LabelEncoder()
    training_data['artist_encoded'] = label_encoder_artist.fit_transform(training_data['artist_name'])
    training_data['track_encoded'] = label_encoder_track.fit_transform(training_data['track_name'])
    
    features = ['popularity', 'artist_encoded', 'track_encoded']
    X = training_data[features]
    
    # Train KNN model
    knn_model = NearestNeighbors(n_neighbors=10, metric='cosine')
    knn_model.fit(X)
    
    # Define recommendation function
    def recommend_songs(user_tracks, knn_model, training_data, top_n=10):
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
    
    # Use recommendation function
    user_top_tracks = ['Comedy', 'Hold On','Say Something','Falling in Love at a Coffee Shop','Lucky','Left for America','あ。っという間はあるさ','Pussy Cat','Look For The Good (Single Version)'] 
    recommended_songs = recommend_songs(user_top_tracks, knn_model, training_data, top_n=5)
    print(recommended_songs)
    
    # Save the model
    model_dir = "./knn_model"
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "knn_model.pkl")
    joblib.dump(knn_model, model_path)

    # Register model to Hopsworks
    try:
        mr = project.get_model_registry()
        model_name = "knn_recommendation_model"
        
        # Check if the model already exists
        try:
            existing_model = mr.get_model(name=model_name)
            print(f"Model '{model_name}' already exists in the Model Registry. Skipping registration.")
        except Exception as e:
            # Assuming that an exception is raised if the model does not exist
            print(f"Model '{model_name}' does not exist. Proceeding to register the model.")
            
            metrics = {
                "Number of neighbors": 10,
            }
            
            knn_recommendation_model = mr.python.create_model(
                name=model_name,       
                metrics=metrics,                       
                input_example=X.iloc[0].values,        
                description=(
                    "Content-based recommendation model using KNN. "
                    "This model uses cosine distance with 10 neighbors."
                ),
            )
            
            knn_recommendation_model.save(model_dir)
            print("KNN recommendation model has been saved to Hopsworks!")
    except Exception as e:
        print(f"Failed to register the model: {e}")

if __name__ == "__main__":
    main()

import hopsworks
import os


os.environ["HOPSWORKS_API_KEY"] = "K86PR55oWoqOXhUX.VUJFWq1zEqfhZntoebWp1RLsH90VVbAYuqukvh5AcM8xHOYk7c4vg4VvD6iZEG37"
project = hopsworks.login()
fs = project.get_feature_store()
print("project.name:")
print(project.name)


feature_group = fs.get_feature_group(name="spotify_features", version=2)
df = feature_group.read()

result = df[df['track_name'] == '路邊的野花']
print(result)

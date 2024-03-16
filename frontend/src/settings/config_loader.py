import json
import os

class ConfigLoader:
    def __init__(self, config_directory="src/config"):
        self.config_directory = config_directory

    def load_config(self, config_name):
        config_path = os.path.join(self.config_directory, f"{config_name}.json")
        try:
            with open(config_path, 'r') as config_file:
                return json.load(config_file)
        except FileNotFoundError:
            print(f"Configuration file {config_path} not found. Using default configuration.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {config_path}. Check file format.")
        return self.default_config(config_name)

    def default_config(self, config_name):
        # Provide default configurations based on the config_name
        defaults = {
            "agraph_viewer": {
                "directed": True,
                "physics": True,
                "hierarchical": False,
                "width": "100%",
                "groups": {
                    "accepted_defendant": {"color": "#ffd966", "shape": "circle"},
                    "defeated_defendant": {"color": "#fff2cc", "shape": "circle"},
                    "accepted_prosecution": {"color": "#16537e", "shape": "circle"},
                    "defeated_prosecution": {"color": "#bfc5ff", "shape": "circle"}
                }
            },
            # Add other default configs here
        }
        return defaults.get(config_name, {})


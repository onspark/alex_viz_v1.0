import json 

class ModelSettings:
    def __init__(self):
        settings_file = "./app/config/model_settings.json"
        self.settings = self.load_settings(settings_file)
    
    def load_settings(self, settings_file):
        with open(settings_file, 'r') as file:
            settings = json.load(file)
        return settings
    
    def get_setting(self, key):
        return self.settings.get(key, None)
    
    def __getitem__(self, key):
        return self.get_setting(key)
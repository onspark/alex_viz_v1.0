import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

class LeapModel:
    "NLI classification model for crime data"
    def __init__(self, model_name_or_path):
        self.model_name_or_path = model_name_or_path
    
    def load_model(self):
        model = AutoModelForSequenceClassification.from_pretrained(self.model_name_or_path)
        return model
    
    def load_tokenizer(self):
        tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path)
        return tokenizer
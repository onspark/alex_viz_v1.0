import torch
# from leap_nli import LeapModel #custom model class
from app.components.tools.leap_nli import LeapModel #custom model class

class LeapPrediction:
    def __init__(self, model_name_or_path):
        self.model_name_or_path = model_name_or_path
        leap_model = LeapModel(self.model_name_or_path)
        self.model = leap_model.load_model()
        self.tokenizer = leap_model.load_tokenizer()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)

    def predict(self, context, sentence):
        MAX_LEN = 128
        tokens = self.tokenizer.encode_plus(context, sentence, max_length=MAX_LEN, return_tensors="pt", truncation=True).to(self.device)
        with torch.no_grad():
            pred_logits = self.model(**tokens)[0]  # Inference
        prediction_result = torch.softmax(pred_logits, dim=1).tolist()[0]
        label, scores = self.get_label_and_score(prediction_result)
        result = {
            'label': label,
            'scores': scores
        }
        return result
    
    def get_label_and_score(self, pred):
        label_names = ["contrasts", "entails", "undetermined"] 
        false_prob = round(pred[0] * 100, 2)
        true_prob = round(pred[1] * 100, 2)
        neutral_prob = round(pred[2] * 100, 2)
        
        label = label_names[pred.index(max(pred))]  # Get final label
        formatted_scores = {"entails": true_prob, "contrasts": false_prob, "undetermined": neutral_prob}
        return label, formatted_scores

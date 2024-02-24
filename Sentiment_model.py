from Base_model import Base_model
from transformers import pipeline

class Sentiment_model(Base_model):
  def __init__(self, model_name, **kwargs) -> None:
    super().__init__(model_name, **kwargs)
    self.top_k = 3

    
  def load(self):
    self.model =  pipeline("text-classification", model=self.path, device=0,  top_k=self.top_k)
     
     
  def generate(self, localContext, callback=None,):
    sentimentList = self.model(localContext)
    sentimentList = sentimentList[0]
    filtered_items = list(filter((lambda x: x["score"] > 0.08), sentimentList))
    sentiment = [x["label"] for x in filtered_items]
    
    return sentiment

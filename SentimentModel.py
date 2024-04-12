from BaseModel import BaseModel
from transformers import pipeline

class SentimentModel(BaseModel):
  def __init__(self, modelName, **kwargs) -> None:
    super().__init__(modelName, **kwargs)
    self.top_k = 3

    
  def load(self):
    self.model =  pipeline("text-classification", model=self.path, device=0,  top_k=self.top_k)
    self.tokenizer = self.model.tokenizer
     
     
  def generate(self, localContext, callback=None,):
    sentimentList = self.model(localContext)
    sentimentList = sentimentList[0]
    filtered_items = list(filter((lambda x: x["score"] > 0.08), sentimentList))
    sentiment = [x["label"] for x in filtered_items]
    
    return sentiment

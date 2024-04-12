from BaseModel import BaseModel
from transformers import AutoTokenizer, AutoModel
from transformers import pipeline

class SummarizationModel(BaseModel):
  def __init__(self, modelName, **kwargs) -> None:
    super().__init__(modelName, **kwargs)
    self.activateable = False
    self.max_length = 256
    self.min_length = 64
    
  def load(self):
    self.model =  pipeline("summarization", model=self.path, device=0)
     
  def generate(self, localContext, callback=None):
    summary = self.model(localContext, min_length=self.min_length,
                         max_length = self.max_length, do_sample=False)[0]["summary_text"]
    if(callback):
      callback(summary)
    return summary

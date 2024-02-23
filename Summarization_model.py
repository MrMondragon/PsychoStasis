from Base_model import Base_model
from transformers import pipeline

class Summarization_model(Base_model):
  def __init__(self, model_name, **kwargs) -> None:
    super().__init__(model_name, **kwargs)
    self.activateable = False
    self.max_length = 256
    self.min_length = 64
    
  def load(self):
    self.model =  pipeline("summarization", model=self.path, device=0)
     
     
  def sliceText(self, text):
    chunkSize = 512
    overlap = 64
    wordList = text.split(" ")
    
    slices = []
    for i in range(0, len(wordList), chunkSize):
      chunks = []
      end = i+chunkSize
      if(i>overlap):
        chunks.extend(wordList[i-overlap:i-1])
      chunks.extend(wordList[i:end])
      if(end+overlap < len(wordList)):
        chunks.extend(wordList[end+1:end+overlap])
      slices.append(" ".join(chunks))
    return slices
      
    
     
  def generate(self, localContext, callback=None):
    
    slices = self.sliceText(localContext)
    summary = ""
    for slice in slices:
      summary += self.model(slice, min_length=self.min_length,
                           max_length = self.max_length, do_sample=False)[0]["summary_text"]+"\n"
      if(callback):
        callback(summary)
    
    return summary

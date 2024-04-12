from BaseModel import BaseModel
from sentence_transformers import SentenceTransformer, util

class EmbeddingsModel(BaseModel):
  def __init__(self, modelName, **kwargs) -> None:
    super().__init__(modelName, **kwargs)
    
  def load(self):
    self.model = SentenceTransformer(self.path, device="cpu")
  
  def ComputeEmbeddings(self, prompts):        
    return self.model.encode(list(prompts), convert_to_numpy=True, normalize_embeddings=True).tolist()
  
  def DecodeEmbeddings(self, embeddings):
    return self.model.decode(embeddings)
    
  def GetSimilarity(self, embeddingsA, embeddingsB):
    return util.cos_sim(embeddingsA, embeddingsB)
  
  #This can be useful in applications such as sentiment analysis, where you want to classify a text 
  # as positive or negative based on the dot product of its embedding with a positive or negative
  # reference embedding.
  def GetDotScore(self, embeddingsA, embeddingsB):
    return util.dot_score(embeddingsA, embeddingsB)
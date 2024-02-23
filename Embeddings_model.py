from Base_model import Base_model
from sentence_transformers import SentenceTransformer, util

class Embeddings_model(Base_model):
  def __init__(self, model_name, **kwargs) -> None:
    super().__init__(model_name, **kwargs)
    
  def load(self):
    self.model = SentenceTransformer(self.path, device="cpu")
  
  def compute_embeddings(self, prompts):        
    return self.model.encode(list(prompts), convert_to_numpy=True, normalize_embeddings=True).tolist()
  
  def decode_embeddings(self, embeddings):
    return self.model.decode(embeddings)
    
  def get_similarity(self, embeddingsA, embeddingsB):
    return util.cos_sim(embeddingsA, embeddingsB)
  
  #This can be useful in applications such as sentiment analysis, where you want to classify a text 
  # as positive or negative based on the dot product of its embedding with a positive or negative
  # reference embedding.
  def get_dot_score(self, embeddingsA, embeddingsB):
    return util.dot_score(embeddingsA, embeddingsB)
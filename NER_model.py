from Base_model import Base_model
from transformers import pipeline
import spacy
import re

class NER_model(Base_model):
  def __init__(self, model_name, **kwargs) -> None:
    super().__init__(model_name, **kwargs)
    self.nlp  = spacy.load(self.params["spacyModel"])
    
  def load(self):
    self.model =  pipeline("ner", model=self.path, tokenizer=self.path, device=0)
     
  def generate(self, localContext, callback=None):
    nerBase = self.model(localContext)
    entities = {}
    entity = {"text":"", "label":""}
    for token in nerBase:
      text = token["word"]
      containsHash = False
      if("#" in text):
        containsHash = True
        text = text.replace("#", "")
      
      label = token["entity"]
      
      if(label.startswith("B-") and not containsHash):
        if(entity["label"] != ""):
          if(len(entity["text"].strip().strip(".,-:;?!").replace('"','').strip()) >2):
            entities[entity["text"].strip().strip(".,-:;?!").strip().lower()] = entity["label"] if entity["label"] != "MISC" else "KEYWORD"
          entity = {"text":"", "label":""}
          
          
      if(containsHash):
        text =entity["text"]+text;  
      else:
        text = entity["text"]+" "+text
        
      entity = {"text":text, "label":label[2:]}
    
    doc = self.nlp(localContext)
    ents = list(str(doc.ents).replace('(', '').replace(')', '').split(", "))
    
    for ent in ents:
      text = ent.strip().strip(".,-").strip().lower().replace('"','')
      text = text.replace("the ", "").replace("this ", "").replace("that ", "")
        
      if(not text in entities):
        number_pattern = r"^(one|two|three|four|five|six|seven|eight|nine|ten|1[0-9]?|20|0\.[1-9])$|^([0-9]{1,3}(,[0-9]{3})*(\.[0-9]+)?)$"
        newText = re.sub(number_pattern, "", text.lower())
        if(newText != "") and (newText != None) and (len(newText) > 2):
          entities[text] = "KEYWORD"
        
    return entities

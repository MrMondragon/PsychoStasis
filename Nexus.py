import glob
from datetime import datetime
import sys
from pathlib import Path


sys.path.insert(0, str(Path(".")))
import os
import json
from CausalLM import CausalLM
from GGUF_model import GGUF_model
from Base_model import Base_model
from Shard_model import Shard_model
from Embeddings_model import Embeddings_model
from Summarization_model import Summarization_model
from NER_model import NER_model
from Sentiment_model import Sentiment_model
import nvidia_smi

model_path = 'models/' 

class Nexus(object):
    def __init__(self):
        self.CortexModel:  Base_model = None
        self.CortexModel_name: str = None
        self.ShardModels: dict[str, Base_model] = {}
        self.load_model("Embeddings.Embeddings")
        self.load_model("Summarizer.Summarizer")
        self.load_model("NER.NER")
        self.load_model("Sentiment.Sentiment")
        
    model_mapping = {
        'Causal' : CausalLM,
        'GGUF' : GGUF_model,
        'Shard' : Shard_model,
        'Embeddings' : Embeddings_model,
        'Summarizer' : Summarization_model,
        'NER' : NER_model,
        'Sentiment': Sentiment_model
    }

    @classmethod
    def get_model_list(cls):    
        # get all files in directory
        files = os.listdir(model_path)
        model_list = [os.path.basename(f) for f in files if f.endswith('.config')]
        return model_list

    @classmethod
    def get_model_class(cls, modelName):
        nameParts = modelName.split('.')
        model_type = nameParts[1]        
        model_class = cls.model_mapping.get(model_type)        
        if(not model_class):
            raise ValueError(f"Invalid model: {model_type}. Supported models: {', '.join(cls.model_mapping.keys())}")          
        return model_class
        
    @classmethod
    def get_model_data(cls, model_name):
        pattern = f"{model_name}*.config"
        # Scan all '.config' files in 'models' directory
        file_list = glob.glob(os.path.join(model_path, pattern))
        filename = file_list[0]
        with open(filename) as f:
            data = json.load(f)
        return data, os.path.basename(filename)
    
    def load_model(self, model_name,  **kwargs):
        if (model_name != self.CortexModel_name) and (model_name not in self.ShardModels):
            data, file_name  = Nexus.get_model_data(model_name)
            core = data["core"]
            model_class = Nexus.get_model_class(file_name)
            # Pass kwargs directly to the constructor
            model = model_class(model_name, **kwargs)
            
            if core:
                model.load()
                model.active = True
                self.CortexModel = model
                self.CortexModel_name = model.model_name
            else:
                self.ShardModels[model_name] = model
                self.ShardModels[model_name].deactivate()

    def unload_model(self, model_name:str):
        if(model_name == self.CortexModel_name):
            self.CortexModel = None
        else:
            model = self.ShardModels[model_name]
            self.ShardModels.pop(model_name)
            model.unload()

    def activate_model(self, model_name:str):
        self.ShardModels[model_name].activate()

    def deactivate_model(self, model_name:str):
        self.ShardModels[model_name].deactivate() 
            
    def get_memory_usage(self):
        nvidia_smi.nvmlInit()
        handle = nvidia_smi.nvmlDeviceGetHandleByIndex(0)  # Assuming a single GPU (index 0)
        info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
        total_memory = info.total / (1024 ** 3)  # Convert bytes to GB
        free_memory = info.free / (1024 ** 3)    # Convert bytes to GB
        used_memory = info.used / (1024 ** 3)    # Convert bytes to GB
        nvidia_smi.nvmlShutdown()
        return {f'total:{total_memory}, free:{free_memory}, used:{used_memory} --- {datetime.now()}'}
 
    def generate_completion_cortex(self, localContext, callback = None, model_name:str = None):
        print(f"performing inference with {self.CortexModel_name}")
        return self.CortexModel.generate(localContext, callback)
    
    def generate_completion_shard(self, localContext, callback = None, model_name:str = None):
        print(f"performing inference with {model_name}")
        self.activate_model(model_name)
        result = self.ShardModels[model_name].generate(localContext, callback)
        print(f"Keep active:{self.ShardModels[model_name].keepActive}")
        if(not self.ShardModels[model_name].keepActive):
            self.deactivate_model(model_name)
        return result
    
    def generate_with_streaming(self, *args, **kwargs):
        yield self.CortexModel.generate_with_streaming(*args, **kwargs)
        
    def compute_embeddings(self, prompts):
        self.activate_model("Embeddings.Embeddings")
        result = self.ShardModels["Embeddings.Embeddings"].compute_embeddings(prompts)
        self.deactivate_model("Embeddings.Embeddings")
        return result
    
    def compute_similarity(self, prompt1 : str, prompt2 : str):
        self.activate_model("Embeddings.Embeddings")
        a = self.ShardModels["Embeddings.Embeddings"].compute_embeddings(prompt1)
        b = self.ShardModels["Embeddings.Embeddings"].compute_embeddings(prompt2)
        result = self.ShardModels["Embeddings.Embeddings"].get_similarity(a, b)
        self.deactivate_model("Embeddings.Embeddings")
        return result
    
    def compute_dotscore(self, prompt1, prompt2):
        self.activate_model("Embeddings.Embeddings")
        a = self.ShardModels["Embeddings.Embeddings"].compute_embeddings(prompt1)
        b = self.ShardModels["Embeddings.Embeddings"].compute_embeddings(prompt2)
        self.deactivate_model("Embeddings.Embeddings")
        result = self.ShardModels["Embeddings.Embeddings"].get_dot_score(a, b)
        return result
    
    def decode_embeddings(self, embeddings):
        self.activate_model("Embeddings.Embeddings")
        result = self.ShardModels["Embeddings.Embeddings"].decode_embeddings(embeddings)
        self.deactivate_model("Embeddings.Embeddings")
        return result

    def summarize(self, prompt):
        self.activate_model("Summarizer.Summarizer")
        result = self.ShardModels["Summarizer.Summarizer"].generate(prompt)
        self.deactivate_model("Summarizer.Summarizer")
        return result
    
    def getNER(self, prompt):
        self.activate_model("NER.NER")
        result = self.ShardModels["NER.NER"].generate(prompt)
        self.deactivate_model("NER.NER")
        return result
    
    def getSentiment(self, prompt):
        self.activate_model("Sentiment.Sentiment")
        result = self.ShardModels["Sentiment.Sentiment"].generate(prompt)
        self.deactivate_model("Sentiment.Sentiment")
        return result
    

        
    
globalNexus = Nexus()

from chromadb.api import EmbeddingFunction, Documents, Embeddings

class NexusEmbeddingFunction(EmbeddingFunction):
  def __call__(self, input: Documents) -> Embeddings:
          return globalNexus.compute_embeddings(input)
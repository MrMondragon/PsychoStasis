import glob
from datetime import datetime
import sys
from pathlib import Path


sys.path.insert(0, str(Path(".")))
import os
import json
from CausalLM import CausalLM
from GGUFModel import GGUFModel
from BaseModel import BaseModel
from ShardModel import ShardModel
from EmbeddingsModel import EmbeddingsModel
from SummarizationModel import SummarizationModel
from NERModel import NERModel
from SentimentModel import SentimentModel
import nvidia_smi
from Logger import globalLogger

model_path = 'models/' 
lora_path = 'lora/' 

class Nexus(object):
    def __init__(self):
        self.CortexModel:  BaseModel = None
        self.CortexModelName: str = None
        self.ShardModels: dict[str, BaseModel] = {}
        self.ShardBatch: dict[str,bool] = {}
        self.LoadModel("Embeddings.Embeddings")
        self.LoadModel("Summarizer.Summarizer")
        self.LoadModel("NER.NER")
        self.LoadModel("SentimentNuanced.Sentiment")
        self.LoadModel("SentimentDiscreet.Sentiment")
        for shard in self.ShardModels:
            self.ShardBatch[shard] = False

        
    modelMapping = {
        'Causal' : CausalLM,
        'GGUF' : GGUFModel,
        'Shard' : ShardModel,
        'Embeddings' : EmbeddingsModel,
        'Summarizer' : SummarizationModel,
        'NER' : NERModel,
        'Sentiment': SentimentModel
    }


    @classmethod
    def GetModelList(cls):    
        # get all files in directory
        files = os.listdir(model_path)
        model_list = [os.path.basename(f) for f in files if f.endswith('.config')]
        return model_list
    
    
    @classmethod
    def GetLoraList(cls):    
        # get all files in directory
        files = os.listdir(lora_path)
        model_list = [os.path.basename(f) for f in files if f.endswith('.gguf')]
        return model_list


    @classmethod
    def GetModelClass(cls, modelName):
        nameParts = modelName.split('.')
        model_type = nameParts[1]        
        model_class = cls.modelMapping.get(model_type)        
        if(not model_class):
            raise ValueError(f"Invalid model: {model_type}. Supported models: {', '.join(cls.modelMapping.keys())}")          
        return model_class

        
    @classmethod
    def GetModelData(cls, modelName):
        pattern = f"{modelName}*.config"
        # Scan all '.config' files in 'models' directory
        file_list = glob.glob(os.path.join(model_path, pattern))
        filename = file_list[0]
        with open(filename) as f:
            data = json.load(f)
        return data, os.path.basename(filename)

    
    def LoadModel(self, modelName,  **kwargs):
        globalLogger.log("loading model " + modelName)
        if (modelName != self.CortexModelName) and (modelName not in self.ShardModels):
            data, file_name  = Nexus.GetModelData(modelName)
            core = data["core"]
            model_class = Nexus.GetModelClass(file_name)
            # Pass kwargs directly to the constructor
            model = model_class(modelName, **kwargs)
            globalLogger.log("model configured")
            if core:
                model.active = False
                self.CortexModel = model
                self.CortexModelName = model.modelName
            else:
                self.ShardModels[modelName] = model
                if("keep_alive" not in model.params):
                    self.ShardModels[modelName].deactivate()


    def UnloadModel(self, modelName:str):
        if(modelName == self.CortexModelName):
            self.CortexModel = None
        else:
            model = self.ShardModels[modelName]
            self.ShardModels.pop(modelName)
            model.unload()


    def ActivateModel(self, modelName:str):
        if(modelName == self.CortexModelName):
            self.CortexModel.activate()
        else:
            self.ShardModels[modelName].activate()


    def DeactivateModel(self, modelName:str):
        if(modelName == self.CortexModelName):
            self.CortexModel.deactivate()
        else:
            self.ShardModels[modelName].deactivate() 

            
    def GetMemoryUsage(self):
        nvidia_smi.nvmlInit()
        handle = nvidia_smi.nvmlDeviceGetHandleByIndex(0)  # Assuming a single GPU (index 0)
        info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
        total_memory = info.total / (1024 ** 3)  # Convert bytes to GB
        free_memory = info.free / (1024 ** 3)    # Convert bytes to GB
        used_memory = info.used / (1024 ** 3)    # Convert bytes to GB
        nvidia_smi.nvmlShutdown()
        return {f'total:{total_memory}, free:{free_memory}, used:{used_memory} --- {datetime.now()}'}

 
    def GenerateCompletionCortex(self, localContext, callback = None, max_tokens = 0, grammar = ""):
        globalLogger.log(f"performing inference with {self.CortexModelName}")
        self.CortexModel.activate()
        self.CortexModel.params["grammar_string"] = grammar        
        return self.CortexModel.generate(localContext, callback, max_tokens=max_tokens)

    
    def GenerateShardCompletion(self, localContext, callback = None, max_tokens = 0, modelName:str = None, grammar = ""):
        globalLogger.log(f"performing inference with {modelName}")
        self.LoadModel(modelName)
        self.ActivateModel(modelName)
        
        if "supports_grammar" in self.ShardModels[modelName].params:
            self.CortexModel.params["grammar_string"] = grammar        
            
        result = self.ShardModels[modelName].generate(localContext, callback, max_tokens=max_tokens)
        if(modelName not in self.ShardBatch) or (not self.ShardBatch[modelName]):
            self.DeactivateModel(modelName)
        return result
    
    
    def BeginShardBatch(self, modelName:str):
        self.ShardBatch[modelName] = True

        
    def EndShardBatch(self, modelName:str):
        self.ShardBatch[modelName] = False
        self.DeactivateModel(modelName)

         
    def ComputeEmbeddings(self, prompts):
        self.ActivateModel("Embeddings.Embeddings")
        result = self.ShardModels["Embeddings.Embeddings"].ComputeEmbeddings(prompts)
        if(not self.ShardBatch["Embeddings.Embeddings"]):
            self.DeactivateModel("Embeddings.Embeddings")
        return result

    
    def ComputeSimilarity(self, prompt1 : str, prompt2 : str):
        self.ActivateModel("Embeddings.Embeddings")
        a = self.ShardModels["Embeddings.Embeddings"].ComputeEmbeddings(prompt1)
        b = self.ShardModels["Embeddings.Embeddings"].ComputeEmbeddings(prompt2)
        result = self.ShardModels["Embeddings.Embeddings"].GetSimilarity(a, b)
        if(not self.ShardBatch["Embeddings.Embeddings"]):
            self.DeactivateModel("Embeddings.Embeddings")
        return result

    
    def ComputeDotScore(self, prompt1, prompt2):
        self.ActivateModel("Embeddings.Embeddings")
        a = self.ShardModels["Embeddings.Embeddings"].ComputeEmbeddings(prompt1)
        b = self.ShardModels["Embeddings.Embeddings"].ComputeEmbeddings(prompt2)
        if(not self.ShardBatch["Embeddings.Embeddings"]):
            self.DeactivateModel("Embeddings.Embeddings")
        result = self.ShardModels["Embeddings.Embeddings"].GetDotScore(a, b)
        return result

    
    def DecodeEmbeddings(self, embeddings):
        self.ActivateModel("Embeddings.Embeddings")
        result = self.ShardModels["Embeddings.Embeddings"].DecodeEmbeddings(embeddings)
        if(not self.ShardBatch["Embeddings.Embeddings"]):
            self.DeactivateModel("Embeddings.Embeddings")
        return result


    def Summarize(self, prompt):
        self.ActivateModel("Summarizer.Summarizer")
        result = self.ShardModels["Summarizer.Summarizer"].generate(prompt)
        if(not self.ShardBatch["Embeddings.Embeddings"]):
            self.DeactivateModel("Embeddings.Embeddings")
        return result

    
    def GetNER(self, prompt):
        self.ActivateModel("NER.NER")
        result = self.ShardModels["NER.NER"].generate(prompt)
        if(not self.ShardBatch["NER.NER"]):
            self.DeactivateModel("NER.NER")
        return result

    
    def TokenizeAndTruncateText(self, text, modelName, size):
        tokenizer = self.ShardModels[modelName].tokenizer
        # Tokenize the input text
        tokenized_text = tokenizer(text, return_tensors='pt', max_length=size, truncation=True)
        # Truncate the tokenized text if needed
        if tokenized_text['input_ids'].shape[1] > size:
            tokenized_text['input_ids'] = tokenized_text['input_ids'][:, :size]
            tokenized_text['attention_mask'] = tokenized_text['attention_mask'][:, :size]
        # Convert token IDs back to text
        decoded_text = tokenizer.decode(tokenized_text['input_ids'][0], skip_special_tokens=True)
        return decoded_text

    
    def GetSentiment(self, prompt, nuanced=True):
        if(nuanced):
            self.ActivateModel("SentimentNuanced.Sentiment")
            prompt = self.TokenizeAndTruncateText(prompt, "SentimentNuanced.Sentiment", 512)
            result = self.ShardModels["SentimentNuanced.Sentiment"].generate(prompt)
            result = "|".join(result)
        else:
            self.ActivateModel("SentimentDiscreet.Sentiment")
            prompt = self.TokenizeAndTruncateText(prompt, "SentimentDiscreet.Sentiment", 512)
            result = self.ShardModels["SentimentDiscreet.Sentiment"].generate(prompt)
            if(len(result) == 2):
                result = "neutral"
            else:
                result = result[0]
        
        return result
    
    
    def CalcTokenSize(self, text):
        encodedText = self.CortexModel.encode(text)
        return len(encodedText), encodedText
        
    
globalNexus = Nexus()


from chromadb.api import EmbeddingFunction, Documents, Embeddings

class NexusEmbeddingFunction(EmbeddingFunction):
  def __call__(self, input: Documents) -> Embeddings:
          return globalNexus.ComputeEmbeddings(input)
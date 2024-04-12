import sys
import os
import glob
import json
from pathlib import Path
sys.path.insert(0, str(Path(".")))
from ContextEntry import ContextEntry

from transformers import AutoTokenizer
from pathlib import Path
from transformers import pipeline
import torch
import gc



class BaseModel:
    def __init__(self, modelName, **kwargs) -> None:
        self.params = kwargs
        self.modelName = modelName
        self.model = None
        self.tokenizer = None
        self.path = None
        self.device:str = ""
        self.active = False
        self.keepActive = False
        
        # Get the current working directory
        cwd = os.getcwd()
        # Define the path to 'models' folder
        models_path = os.path.join(cwd, "models")
        # Build the pattern for glob function
        pattern = f"{modelName}*.config"
        
        # Scan all '.config' files in 'models' directory
        file_list = glob.glob(os.path.join(models_path, pattern))
        
        if file_list:  # If list is not empty
            filename = file_list[0]  # Return the first file found        
            with open(filename) as f:
                data = json.load(f)
                if("params" in data):
                    for key, value in data['params'].items():
                        if key not in self.params:
                            self.params[key] = value
                self.path = data['path']
                   
    def load(self):
        pass
    

    def activate(self):
        if(not self.active):
            self.load()
            self.active = True
            print(f"model {self.modelName} activated")
        
    def deactivate(self):
        if(self.active):
            self.unload()
            self.active = False
            print(f"model {self.modelName} deactivated")
        
    def unload(self):
        del self.model
        self.model = None
        self.clean_up()
        
    def clean_up(self):
        torch.cuda.empty_cache()
        gc.collect() 
    
    def pipeline(self, task, text, execution_args = {}, **kwargs):
        pipe_task = pipeline(task, model = self.model, tokenizer = self.tokenizer, kwargs=kwargs)
        return pipe_task(text,**execution_args)                
    
    def load_tokenizer(self):
    # Loading the tokenizer
        tokenizer = AutoTokenizer.from_pretrained(str(Path(self.path)))
        tokenizer.truncation_side = 'left'
        self.tokenizer = tokenizer
        
    @classmethod
    def get_max_memory_dict(cls):
        max_memory = {}
        max_memory[0] = '20GiB'
        max_memory['cpu'] = '64GiB'
        return max_memory
    
    def generate(self, localContext, callback=None, max_tokens = 0):
        pass
        
    def reset():
        pass
    
    def FormatAnswer(self, answer, role, context):
        id = answer["id"]
        id = id.replace("chatcmpl", role)
        msg = answer["choices"][0]["message"]["content"]
        if(msg):
            while r"\n" in msg:
                msg = msg.replace(r"\n", "\n")
            
        if(msg.startswith(f"{role}: ")):
            msg=msg.replace(f"{role}: ", "")
        
        return ContextEntry(role=role, content=msg, roleName=role, id=id, context=context)
    
        
    
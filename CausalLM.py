import sys
from pathlib import Path
sys.path.insert(0, str(Path(".")))

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path
from BaseModel import BaseModel
from Logger import globalLogger, LogLevel

class CausalLM(BaseModel):
    def __init__(self, modelName, **kwargs) -> None:
        super().__init__(modelName, **kwargs)
        self.params['low_mem'] = False if 'low_mem' not in self.params else self.params['low_mem']
        self.params['max_length'] = 2048 if 'max_length' not in self.params else self.params['max_length']
        self.params['bf16'] = True if 'bf16' not in self.params else self.params['bf16']
        self.params['load_in_8bit'] = True if 'load_in_8bit' not in self.params else self.params['load_in_8bit']

    def load(self):
        model = AutoModelForCausalLM.from_pretrained(self.path)
        torch.set_default_device('cuda')
        model = model.cuda()
        
        self.model = model
        self.tokenizer = AutoTokenizer.from_pretrained(self.path)
    
    def encode(self, prompt):
        return self.tokenizer.encode(prompt, return_tensors='pt')
    
    def decode(self, ids):
        return self.tokenizer.decode(ids, skip_special_tokens=True) 
        
    def generate(self, localContext, callback=None):
        
        prompt = ""
        for message in localContext:
            prompt += message["role"] + ": " + message["content"]+"\n"
        
        globalLogger.log(logLevel=LogLevel.globalLog, message=prompt)
        
        device = next(self.model.parameters()).device.type
        
        input_ids = self.tokenizer.encode(prompt, add_special_tokens=False,return_tensors='pt')
        input_ids = input_ids.to(device)
        
        output = self.model.generate(input_ids,                                      
                                     do_sample=True,
                                     max_length=self.params["max_length"],
                                     temperature=self.params["temperature"],
                                     top_p=self.params["top_p"],
                                     top_k=self.params["top_k"],
                                     repetition_penalty=self.params["repetition_penalty"],
                                     length_penalty=self.params["length_penalty"],
                                     early_stopping=self.params["early_stopping"],
                                     num_beams=self.params["num_beams"],
                                     no_repeat_ngram_size=self.params["no_repeat_ngram_size"],
                                     num_return_sequences=self.params["num_return_sequences"]) 
        text = self.tokenizer.decode(output[0], skip_special_tokens=True)
        
        if callback:
            callback(text)
        globalLogger.log(logLevel=LogLevel.globalLog, message=text)
        return text
        
        
        
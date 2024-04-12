import os
import re
from functools import partial
import numpy as np
import torch
import RoPE
from callbacks import Iteratorize

try:
    import llama_cpp
except:
    llama_cpp = None

try:
    import llama_cpp_cuda
except:
    llama_cpp_cuda = None

try:
    import llama_cpp_cuda_tensorcores
except:
    llama_cpp_cuda_tensorcores = None
    
from BaseModel import BaseModel

lora_path="LoRa/"
    
def ban_eos_logits_processor(eos_token, logits):
    logits[eos_token] = -float('inf')
    return logits


def custom_token_ban_logits_processor(token_ids, logits):
    for token_id in token_ids:
        logits[token_id] = -float('inf')

    return logits    

def get_max_localContext_length(params):
    return params['truncation_length'] - params['max_new_tokens']  
    
class GGUFModel(BaseModel):
    def __init__(self, modelName, **kwargs) -> None:
        super().__init__(modelName, **kwargs)
        ##
        self.params['cpu'] = False if 'cpu' not in self.params else self.params['cpu']
        self.params['tensorcores'] = False if 'tensorcores' not in self.params else self.params['tensorcores']
        self.params['n_ctx'] = 2048 if 'n_ctx' not in self.params else self.params['n_ctx']
        self.params['threads'] = 20 if 'threads' not in self.params else self.params['threads']
        self.params['threads-batch'] = 10 if 'threads-batch' not in self.params else self.params['threads-batch']
        ##
        self.params['no_mul_mat_q'] = False if 'no_mul_mat_q' not in self.params else self.params['no_mul_mat_q']
        self.params['n_batch'] = 512 if 'n_batch' not in self.params else self.params['n_batch']
        ##
        self.params['no-mmap'] = True if 'no-mmap' not in self.params else self.params['no-mmap']
        self.params['mlock'] = False if 'mlock' not in self.params else self.params['mlock']
        self.params['n-gpu-layers'] = -1 if 'n-gpu-layers' not in self.params else self.params['n-gpu-layers']
        self.params['tensor_split'] = None if 'tensor_split' not in self.params else self.params['tensor_split']
        #
        self.params['numa'] = True if 'numa' not in self.params else self.params['numa']
        self.params['logits_all'] = False if 'logits_all' not in self.params else self.params['logits_all']
        self.params['cache-capacity'] = '60GiB' if 'cache-capacity' not in self.params else self.params['cache-capacity']
        self.params['no_offload_kqv'] = False if 'no_offload_kqv' not in self.params else self.params['no_offload_kqv']
        
        self.params['alpha_value'] = 1 if 'alpha_value' not in self.params else self.params['alpha_value']
        self.params['rope_freq_base'] = 0 if 'rope_freq_base' not in self.params else self.params['rope_freq_base']
        self.params['compress_pos_emb'] = 1 if 'compress_pos_emb' not in self.params else self.params['compress_pos_emb']
        self.params['chat_format'] =  "llama-2" if 'chat_format' not in self.params else self.params['chat_format']
        self.params['max_tokens'] =  1024 if 'max_tokens' not in self.params else self.params['max_tokens']
        self.params['LoRa'] =  "" if 'LoRa' not in self.params else self.params['LoRa']
        
        self.initialized = False
        self.grammar_string = ''
        self.grammar = None
        self.user_token = "[you]"
        self.streaming = False
        self.gpuLayers =self.params['n-gpu-layers']

    def __del__(self):
        del self.model
      
    def llama_cpp_lib(self):
        if self.params['cpu'] and llama_cpp is not None:
            return llama_cpp
        elif self.params['tensorcores'] and llama_cpp_cuda_tensorcores is not None:
            return llama_cpp_cuda_tensorcores
        elif llama_cpp_cuda is not None:
            return llama_cpp_cuda
        else:
            return llama_cpp
  
    def load(self):
        Llama = self.llama_cpp_lib().Llama
        
        
        
        if(self.params['LoRa'] != ""):
            #cwd = os.getcwd()
            #lora_path = os.path.join(cwd, lora_path, self.params['LoRa'])
            Llama.lora_path = self.params['LoRa'] #lora_path            
        else:
            Llama.lora_path = None
            
        print("LoRa: ", Llama.lora_path)
            
        LlamaCache = self.llama_cpp_lib().LlamaCache 

        cache_capacity = 0

        if self.params['cache-capacity'] is not None:
            if 'GiB' in self.params['cache-capacity']:
                cache_capacity = int(re.sub('[a-zA-Z]', '', self.params['cache-capacity'])) * 1000 * 1000 * 1000
            elif 'MiB' in self.params['cache-capacity']:
                cache_capacity = int(re.sub('[a-zA-Z]', '', self.params['cache-capacity'])) * 1000 * 1000
            else:
                cache_capacity = int(self.params['cache-capacity'])    

            if self.params['tensor_split']  is None or self.params['tensor_split'].strip() == '':
                tensor_split_list = None
            else:
                tensor_split_list = [float(x) for x in self.params['tensor_split'].strip().split(",")]            

            params = {
                'model_path': str(self.path),
                'lora_base': str(self.path),
                'n_ctx': self.params['n_ctx'],
                'n_threads': self.params['threads'] or None,
                'n_threads_batch': self.params['threads-batch'] or None,
                'n_batch': self.params['n_batch'],
                'use_mmap': not self.params['no-mmap'],
                'use_mlock': self.params['mlock'],
                'mul_mat_q': not self.params['no_mul_mat_q'],
                'numa': self.params['numa'],
                'n_gpu_layers': self.params['n-gpu-layers'],
                'rope_freq_base': RoPE.get_rope_freq_base(self.params['alpha_value'], self.params['rope_freq_base']),
                'tensor_split': tensor_split_list,
                'rope_freq_scale': 1.0 / self.params['compress_pos_emb'],
                'chat_format': self.params['chat_format'],
            }            
            print(params)
            self.model = Llama(**params)
            self.tokenizer = self.model
            if(cache_capacity > 0):
                self.model.set_cache(LlamaCache(cache_capacity))
            self.reset()
            
   
    def generate(self, localContext, callback=None, max_tokens = 0):
        super().generate(localContext, callback)
        LogitsProcessorList = self.llama_cpp_lib().LogitsProcessorList

        # Handle truncation
        #localContext = self.encode(localContext)
        #localContext = localContext[-get_max_localContext_length(self.params):]
        #localContext = self.decode(localContext)

        if("grammar_string" in self.params): 
            self.load_grammar(self.params['grammar_string'])
            
        logit_processors = LogitsProcessorList()
        if self.params['ban_eos_token']:
            logit_processors.append(partial(ban_eos_logits_processor, self.model.token_eos()))

        if self.params['custom_token_bans']:
            to_ban = [int(x) for x in self.params['custom_token_bans'].split(',')]
            if len(to_ban) > 0:
                logit_processors.append(partial(custom_token_ban_logits_processor, to_ban))

       
        completion_chunks = self.model.create_chat_completion(
            messages=localContext,
            max_tokens=self.params['max_tokens'] if max_tokens == 0 else max_tokens,
            temperature=self.params['temperature'],
            top_p=self.params['top_p'],
            min_p=self.params['min_p'],
            typical_p=self.params['typical_p'],
            frequency_penalty=self.params['frequency_penalty'],
            presence_penalty=self.params['presence_penalty'],
            repeat_penalty=self.params['repetition_penalty'],
            top_k=self.params['top_k'],
            #stream=self.streaming,
            seed=int(self.params['seed']) if self.params['seed'] != -1 else None,
            tfs_z=self.params['tfs'],
            mirostat_mode=int(self.params['mirostat_mode']),
            mirostat_tau=self.params['mirostat_tau'],
            mirostat_eta=self.params['mirostat_eta'],
            logits_processor=logit_processors,
            stop=["[user]", "[system]", "[context]",f"[{self.user_token}]"],
            grammar=self.grammar
        )

        output = completion_chunks
        
        
        
        #if(self.streaming):
        #    text = ""
        #    for completion_chunk in completion_chunks:
        #        #if callbacks.stop_everything:
        #        #    break
        #        text = completion_chunk['choices'][0]['text']
        #        text += text
        #        if callback:
        #            callback(text)
        #        yield text


        return output

    def encode(self, string):
        if type(string) is str:
            string = string.encode()
        return self.model.tokenize(string)

    def decode(self, ids):
        return self.model.detokenize(ids).decode('utf-8')   
    
    def get_logits(self, tokens):
        self.model.reset()
        self.model.eval(tokens)
        logits = self.model._scores
        logits = np.expand_dims(logits, 0)  # batch dim is expected
        return torch.tensor(logits, dtype=torch.float32)   
    
    def load_grammar(self, string):
        if string != self.grammar_string:
            self.grammar_string = string
            if string.strip() != '':
                self.grammar = self.llama_cpp_lib().LlamaGrammar.from_string(string)
            else:
                self.grammar = None     

    def generate_with_streaming(self, *args, **kwargs):
        self.streaimng = True
        with Iteratorize(self.generate, args, kwargs, callback=None) as generator:
            reply = ''
            for token in generator:
                reply += token
                yield reply  
        self.streaimng = False
        
    def reset(self):
        self.model.cache = None
    
    

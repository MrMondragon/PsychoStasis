import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
from Nexus import Nexus

class test_GPT(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls) -> None:
       cls.mm.LoadModel(modelName="gpt-neo-1.3B",model_type= "GPT", core= True, task='')
       return super().setUpClass()

    mm = Nexus()
    
    def test_a_activeGPT(self):
        self.mm.ActivateModel(modelName="gpt-neo-1.3B", core=True)
        self.assertIsNotNone(self.mm.active_core)
        self.assertTrue(self.mm.active_core.device == "cuda")
        
    def test_b_deactivateGPT(self):
         used_memory = self.mm.GetMemoryUsage()['used']
         self.mm.DeactivateModel(modelName="gpt-neo-1.3B", core=True)
         self.assertIsNone(self.mm.active_core)
         self.assertTrue(self.mm.BaseModels["gpt-neo-1.3B"].device == "cpu")
         new_used_memory = self.mm.GetMemoryUsage()['used']
         self.assertLess(new_used_memory, used_memory)
    
    def test_c_unloadGPT(self):
        self.mm.LoadModel(modelName="gpt-neo-1.3B",model_type= "GPT", core= True, task='')
        used_memory = self.mm.GetMemoryUsage()['used']
        self.mm.UnloadModel(modelName="gpt-neo-1.3B", core=True)
        new_used_memory = self.mm.GetMemoryUsage()['used']
        self.assertLess(new_used_memory, used_memory)
        
class test_GPTQ(unittest.TestCase):
    
    def test_a_LoadGPTQ(self):
        mm = Nexus()
        mm.LoadModel(modelName="vicuna-13b-GPTQ-4bit-128g",model_type= "GPTQ", core= True, task='')
        mm.ActivateModel(modelName="vicuna-13b-GPTQ-4bit-128g", core=True)
        self.assertIsNotNone(mm.active_core)
        self.assertTrue(mm.active_core.device == "cuda")
        
class test_30B(unittest.TestCase):
    def test_a_Load30b(self):
        mm = Nexus()
        mm.LoadModel(modelName="llama-wizard-13b-4bit-gr128",model_type= "GPTQ", core= True, task='')
        mm.ActivateModel(modelName="llama-wizard-13b-4bit-gr128", core=True)
        self.assertIsNotNone(mm.active_core)
        self.assertTrue(mm.active_core.device == "cuda")
        
class test_RWKV(unittest.TestCase):
    def test_a_LoadRWKV(self):
        mm = Nexus()
        mm.LoadModel(modelName="RWKV-4-Raven-3B", model_type= "RWKV", core= False, task='')

class test_base_functions(unittest.TestCase):
    
    def test_model_list(self):
        list = Nexus.GetModelList()
        for model in list:
            print(model)
        
        self.assertGreater(len(list), 0)
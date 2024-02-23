import glob
import importlib
import json
import os



process_path = 'CognitiveProcesses/'

class CognitiveSystem(object):
  def __init__(self) -> None:
    self.processes = {}
    self.processConfigs = {}    
    self.commonProcesses = []
    self.LoadProcessConfigs()
    

  def RunProcesses(self, proxy, context):
    processes = list(filter(lambda proc: (context in proc["contexts"])
                            and ((proc["name"] in proxy.cognitiveProcs) 
                            or (proc["name"] in self.commonProcesses)), self.processConfigs.values()))
                            
    if processes:
      for proc in processes:
        process =self.InstantiateProcess(proc["name"])
        process.Run(proxy)
      
  def LoadProcessConfigs(self):
    cwd = os.getcwd()
    workPath = os.path.join(cwd, process_path) 
    pattern = f"*.process"    
    fileList = glob.glob(os.path.join(workPath, pattern))    
    if fileList:  # If list is not empty
      for filename in fileList:
        with open(filename) as f:
          data = json.load(f)
          procName = data["name"]          
          self.processConfigs[procName] = data
          if(data["common"]):
            self.commonProcesses.append(procName)          
      
  def InstantiateProcess(self, procName):
    if(not procName in self.processes):
      procCfg = self.processConfigs[procName]      
      module = importlib.import_module(procName)
      cls = getattr(module, procName)
      procObject = cls(name=procCfg, kwargs=self.processConfigs[procName])
      self.processes[procName] = procObject
    else:
      procObject = self.processes[procName]
    return procObject
  
  def RegisterCommonProcesses(self, proxy):
    if(self.commonProcesses):
      for proc in self.commonProcesses:
        proxy.cognitiveProcs.append(proc)


cognitiveSystem = CognitiveSystem()  

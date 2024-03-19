import glob
import importlib
import json
import sys
import os


class DynamicSystem(object):
  def __init__(self, **kwargs) -> None:
    self.processes = {}
    self.LoadProcesses(self.getProcessPath(), **kwargs)
  
  
  def getProcessPath(self):
    return ""
  
  def LoadProcesses(self, processPath, **kwargs):
    cwd = os.getcwd()
    workPath = os.path.join(cwd, processPath) 

    pattern = "*.py"
    fileList = glob.glob(os.path.join(workPath, pattern))
    if fileList:  # If list is not empty
    
      abstractModuleName = list(filter(lambda x: os.path.basename(x).startswith('_')
                                  and not '__init__.py' in x, fileList))
      concreteModules = list(filter(lambda x: not os.path.basename(x).startswith('_'), fileList))
      
      if(abstractModuleName):
        abstractModuleName = abstractModuleName[0]
        #abstractModule =  os.path.splitext(os.path.basename(abstractModule))[0]
        
        abstractProcName = os.path.splitext(os.path.basename(abstractModuleName))[0]
        abstractSpec = importlib.util.spec_from_file_location(abstractProcName, abstractModuleName)
        abstractModule = importlib.util.module_from_spec(abstractSpec)
        abstractSpec.loader.exec_module(abstractModule)
        sys.modules[abstractProcName] = abstractModule
      
      for fileName in concreteModules:
        procName = os.path.splitext(os.path.basename(fileName))[0]        
        module = importlib.import_module(processPath+"."+procName)        
        cls = getattr(module, procName)
        cfg = fileName.replace(".py", ".config")
        if(os.path.isfile(cfg)):
          kwargs = json.load(open(cfg))
        procObject = cls(**kwargs)
        self.processes[procName] = procObject
          
from DynamicSystem import DynamicSystem
from collections import deque

class CognitiveSystem(DynamicSystem):
  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.commonProcesses = []
    self.stack = deque()
    self.params = {}
    self.params["system"] = "system1"
    
    comonProcesses = list(filter(lambda proc: proc.common, self.processes.values()))
    for proc in comonProcesses:
      self.commonProcesses.append(proc.Name)

  def RunProcesses(self, proxy, context):
    self.params = {}
    self.params["system"] = "system1"
    processes = list(filter(lambda proc: (context in proc.contexts)
                            and ((proc.Name in proxy.cognitiveProcs) 
                            or (proc.Name in self.commonProcesses)), self.processes.values()))
    
    if(proxy.collective != None):
      processes = list(filter(lambda proc: ((proc.Name not in proxy.collective.cognitiveProcs) and
                                            (proc.Name not in self.commonProcesses)), processes))
    if processes:
      processes.sort(key=lambda proc: proc.priority)
      self.stack = deque()
      self.stack.extend(processes)
      while(len(self.stack) > 0):
        proc = self.stack.popleft()
        proc.Run(proxy)
  
  def getProcessPath(self):
    return "/CognitiveProcesses/"


cognitiveSystem = CognitiveSystem()  

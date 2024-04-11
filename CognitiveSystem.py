from DynamicSystem import DynamicSystem
from collections import deque

class CognitiveSystem(DynamicSystem):
  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    commonProcesses = list(filter(lambda proc: proc.common, self.processes.values()))
    self.commonProcesses = list(map(lambda proc: proc.Name, commonProcesses))
    self.stack = deque()
    self.params = {}

  def RunProcess(self, proxy, procName):
    if(procName in self.processes):
      proc = self.processes[procName]
      return proc.Run(proxy)
    

  def RunProcesses(self, proxy, context):
    print(f"Running processes in context {context}")
    self.params = {}
    
    processes = self.processes.values()
    print(f"All procs: {'|'.join(proc.Name for proc in processes)}")
    processes = list(filter(lambda proc: (context in proc.contexts), processes))
    print(f"Context filtered procs: {'|'.join(proc.Name for proc in processes)}")
    processes = list(filter(lambda proc: ((proc.Name in proxy.cognitiveProcs) or (proc.Name in self.commonProcesses)), processes))
    print(f"Proxy and common filtered procs: {'|'.join(proc.Name for proc in processes)}")
  
    
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
    return "CognitiveProcesses"


cognitiveSystem = CognitiveSystem()  

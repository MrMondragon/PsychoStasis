from DynamicSystem import DynamicSystem
from collections import deque
from Logger import globalLogger, LogLevel
import traceback

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
    try:
      globalLogger.log(logLevel=LogLevel.cognitiveLog, message=f"Running processes in context {context}")
      self.params = {}
      
      processes = self.processes.values()
      globalLogger.log(logLevel=LogLevel.cognitiveLog, message=f"All procs: {'|'.join(proc.Name for proc in processes)}")
      processes = list(filter(lambda proc: (context in proc.contexts), processes))
      globalLogger.log(logLevel=LogLevel.cognitiveLog, message=f"Context filtered procs: {'|'.join(proc.Name for proc in processes)}")
      processes = list(filter(lambda proc: ((proc.Name in proxy.cognitiveProcs) or (proc.Name in self.commonProcesses)), processes))
      globalLogger.log(logLevel=LogLevel.cognitiveLog, message=f"Proxy and common filtered procs: {'|'.join(proc.Name for proc in processes)}")
      
      if(proxy.collective != None):
        processes = list(filter(lambda proc: ((proc.Name not in proxy.collective.cognitiveProcs) and
                                              (proc.Name not in self.commonProcesses)), processes))
      if processes:
        for process in processes:
          localContext = proxy.context.GetUncommitedMessages(processName = process.Name, frequency = process.frequency)
          if(len(localContext)>0):
            process.localContext = localContext
          else:
            process.localContext = None
        
        processes = list(filter(lambda proc: proc.localContext is not None, processes))
        if(len(processes) > 0):
          processes.sort(key=lambda proc: proc.priority)
          try:
            processToRun = processes[0]
            processToRun.frequency+= 100
            processToRun.Run(proxy)
          except Exception as e:
            globalLogger.log(message = f"Error running process {process.Name} in context {context} for proxy {proxy}: {e}", logLevel=LogLevel.errorLog)
            globalLogger.log(message = traceback.format_exc(), logLevel=LogLevel.errorLog)
    except Exception as e:
      globalLogger.log(message = f"Error running processes in context {context}: {e}", logLevel = LogLevel.errorLog)
      globalLogger.log(message = traceback.format_exc(), logLevel = LogLevel.errorLog)
  
  def getProcessPath(self):
    return "CognitiveProcesses"


cognitiveSystem = CognitiveSystem()  

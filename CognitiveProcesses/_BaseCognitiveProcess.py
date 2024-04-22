import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
from Nexus import globalNexus
from LongTermMemory import longTermMemory
import grammars
from Logger import globalLogger, LogLevel


class BaseCognitiveProcess(object):
  def __init__(self, **kwargs) -> None:
    self.DecisoryStatement = "" if "DecisoryStatement" not in kwargs else kwargs["decisoryStatement"] 
    self.Shard = None if "Shard" not in kwargs else kwargs["shard"]
    self.Contexts = [] if "contexts" not in kwargs else kwargs["contexts"]
    self.SubProcesses = [] if "subProcesses" not in kwargs else kwargs["subProcesses"]
    self.frequency = 50 if "frequency" not in kwargs else kwargs["frequency"]
    self.Name = "name"
    self.ShouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.proxy= None
    self.priorty = 100 if "priority" not in kwargs else kwargs["priority"]
    self.localContext = None
  
  def Run(self, proxy):
    self.proxy = proxy
    globalLogger.log(logLevel=LogLevel.cognitiveLog, message=f"Running {self.Name} with local context {len(self.localContext)} and frequency = {self.frequency}")
    
    if(self.frequency == -1):
      return    
    if(self.ShouldRun):
      globalLogger.log(logLevel=LogLevel.cognitiveLog, message=f"Engaging in {self.Name} Cognitive Process")
      result = self._internalRun()
    else:
      result = None
    self.proxy.commitContext()
    self.proxy = None
    return result
 
  
  def ShouldRun(self):
    if self.ShouldRun:
      return self.frequency !=  -1
    else:
      return False
    
  def _internalRun(self):
    if(self.proxy.context.verbose):
      globalLogger.log(logLevel=LogLevel.cognitiveLog, message=f"Internal execution for {self.Name}")
      
  def getUncommitedContext(self):
    context = self.proxy.context 
    globalLogger.log(logLevel=LogLevel.cognitiveLog, message=f"Getting uncommited messages for {self.Name} - frequency = {self.frequency}")
    ## for testing purposes
    if(self.frequency == 0):
      return context.messageHistory
    if(self.frequency == -1):
      return []
    
    interactions = context.GetUncommitedMessages(self.Name, self.frequency)
    return interactions
    
  def judgeMessages(self, localContext, prompt, copySystem=True, deepCopy = False, 
                    resetCortex=True):
    self.Grammar = grammars.yesNo
    self.proxy.enterSubContext(deepCopy=deepCopy, resetCortex=resetCortex, 
                               copySystem=copySystem, interactions=localContext)
    answer = self.proxy.GenerateAnswer(shard=self.Shard, prompt=prompt)
    self.proxy.exitSubContext()
    boolAnswer = self.sentenceToBoolean(answer)
    return boolAnswer
  
  def sentenceToBoolean(self, choice):
    query = longTermMemory.booleanDiscriminationMemory.query(query_texts=[choice], n_results=1, where=[], include=[])
    id = query["ids"][0][0]
    if(id == "1"):
      return True
    else:
      return False

  def getClosestWord(self, sentence, top_k=1):
    query = longTermMemory.closestWordMemory.query(query_texts=[sentence], 
                                         n_results=top_k, where=[], include=["documents"])
    word = query["documents"][0]
    return word    

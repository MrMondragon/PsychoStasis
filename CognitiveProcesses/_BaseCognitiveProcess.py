import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
from Nexus import globalNexus
from Memory import globalMemory
import grammars

class BaseCognitiveProcess(object):
  def __init__(self, **kwargs) -> None:
    self.DecisoryStatement = "" if "DecisoryStatement" not in kwargs else kwargs["decisoryStatement"] 
    self.Shard = None if "Shard" not in kwargs else kwargs["shard"]
    if(self.Shard):
      globalNexus.load_model(self.Shard)
    self.Contexts = [] if "contexts" not in kwargs else kwargs["contexts"]
    self.SubProcesses = [] if "subProcesses" not in kwargs else kwargs["subProcesses"]
    self.Frequency = 1 if "frequency" not in kwargs else kwargs["frequency"]
    self.Name = "name"
    self.ContextCallback = self.ExpandContext
    self.ShouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.innerThoughts = False
    self.proxy= None
    self.priorty = 100 if "priority" not in kwargs else kwargs["priority"]
  
  def Run(self, proxy, **kwargs):
    
    self.proxy = proxy
    localContext = self.getLocalContext()
    if(localContext == []):
      return
    
    if("innerThoughts" in kwargs):
      self.innerThoughts = kwargs["innerThoughts"]
    if(self.ShouldRun):
      self._internalRun(localContext)   
   
    self.proxy = None
      
  
  def ExpandContext():
    pass  
  
  def ConditionalRunSubProcesses(self):
    if(self.SubProcesses):
      decisoryStatement = "If applicable, you now have the following options:\n"
      for subProcess in self.SubProcesses:
        decisoryStatement += f"Name: {subProcess.Name} - {subProcess.DecisoryStatement}\n"
      decisoryStatement += "Respond with the Name of the option if any applies or respond with none if no option applies\n"
      
      prompt = decisoryStatement
      
      decision = self.proxy.GenerateAnswer(prompt= prompt, shard=self.Shard, contextCallback = self.contextCallback, innerThoughts = self.innerThoughts)
      if(decision.lower() != "none"):
        choice = self.ChooseSubProcess(decision)
        if(not choice):
          prompt += "You have chosen an invalid option. Please try again.\n"
          decision = self.proxy.GenerateAnswer(prompt= prompt, shard=self.Shard, contextCallback = self.contextCallback, innerThoughts = self.innerThoughts)
          choice = self.ChooseSubProcess(decision)
        if(choice):
          choice.Run()
          

  def ChooseSubProcess(self, decision):
      choice = next((subProcess for subProcess in self.SubProcesses 
                      if decision.lower().contains(subProcess.Name.lower())), None)
      
      if(choice & self.proxy.context.verbose):
        print(f"SubCognitiveProcess {choice.Name} selected")      
      return choice
  
  def ShouldRun(self):
    if self.ShouldRun:
      return
    else:
      if(self.proxy.context.verbose):
        print(f"Running decisory process for {self.Name}")
      result = True    
      if(self.DecisoryStatement):
        prompt = f"You now have the option to {self.DecisoryStatement}. Is it applicable?  Answer with yes or no only."
        decision = self.proxy.GenerateAnswer(prompt= prompt, shard=self.Shard, contextCallback = self.contextCallback, innerThoughts = self.innerThoughts)
        result = globalMemory.sentenceToBoolean(decision)
    
      if(self.proxy.context.verbose):
        print(f"Result = {result}")
    
  def _internalRun(self):
    if(self.proxy.context.verbose):
      print(f"Internal execution for {self.Name}")
      
  def getLocalContext(self):
    context = self.proxy.context if not self.innerThoughts else self.proxy.innerThoughts
    
    interactions = context.proxyInteractionCounter[self.proxy.name]
    
    if(interactions%self.frequency == 0):
      freq = self.frequency * -1
      localContext = context.message_history[freq:]
      return localContext
    else:
      return []
    
  def judgeMessages(self, localContext, prompt, copySystem=True, deepCopy = False, 
                    resetCortex=True, start=None, end=None):
    self.Grammar = grammars.yesNo
    self.proxy.enterSubContext(deepCopy=deepCopy, resetCortex=resetCortex, 
                               copySystem=copySystem, start=start, end=end)
    self.proxy.context.message_history.extend(localContext)
    answer = self.proxy.GenerateAnswer(shard=self.Shard, prompt=prompt)
    self.proxy.exitSubContext()
    boolAnswer = self.sentenceToBoolean(answer)
    return boolAnswer
  
  def sentenceToBoolean(self, choice):
    query = globalMemory.booleanDiscriminationMemory.query(query_texts=[choice], n_results=1, where=[], include=[])
    id = query["ids"][0][0]
    if(id == "1"):
      return True
    else:
      return False

  def getClosestWord(self, sentence, top_k=1):
    query = globalMemory.closestWordMemory.query(query_texts=[sentence], 
                                         n_results=top_k, where=[], include=["documents"])
    word = query["documents"][0]
    return word    

import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
from Nexus import globalNexus
from Memory import globalMemory
from Proxy import Proxy

class BaseCognitiveProcess(object):
  def __init__(self, procConfig) -> None:
    self.DecisoryStatement = "" if "DecisoryStatement" not in procConfig else procConfig["decisoryStatement"] 
    self.Shard = None if "Shard" not in procConfig else procConfig["shard"]
    if(self.Shard):
      globalNexus.load_model(self.Shard)
    self.Grammar = None
    self.SubProcesses = [] if "subProcesses" not in procConfig else procConfig["subProcesses"]
    self.Frequency = "" if "frequency" not in procConfig else procConfig["frequency"]
    self.Name = procConfig["name"]
    self.contextCallback = self.ExpandContext
    self.shouldRun = True if "shouldRun" not in procConfig else procConfig["shouldRun"]
    self.proxy: Proxy = None
  
  def Run(self, proxy):
    self.proxy = proxy
    if(self.ShouldRun(proxy)):
      oldGrammar = ""
      if(self.Grammar):
        if(not self.Shard):
          oldGrammar = globalNexus.CortexModel.params['grammar_string']
          globalNexus.CortexModel.params['grammar_string'] = self.Grammar
        else:
          oldGrammar = globalNexus.ShardModels[self.Shard].params['grammar_string']
          globalNexus.ShardModels[self.Shard].params['grammar_string'] = self.Grammar
          
      self._internalRun()  
      self.ConditionalRunSubProcesses()  
      if(not self.Shard):
        globalNexus.CortexModel.params['grammar_string'] = oldGrammar
      else:
        globalNexus.ShardModels[self.Shard].params['grammar_string'] = oldGrammar
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
      
      decision = self.proxy.GenerateAnswer(prompt= prompt, shard=self.Shard, contextCallback = self.contextCallback, innerThoughts = False)
      if(decision.lower() != "none"):
        choice = self.ChooseSubProcess(decision)
        if(not choice):
          prompt += "You have chosen an invalid option. Please try again.\n"
          decision = self.proxy.GenerateAnswer(prompt= prompt, shard=self.Shard, contextCallback = self.contextCallback, innerThoughts = False)
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
    if self.shouldRun:
      return
    else:
      if(self.proxy.context.verbose):
        print(f"Running decisory process for {self.Name}")
      result = True    
      if(self.DecisoryStatement):
        prompt = f"You now have the option to {self.DecisoryStatement}. Is it applicable?  Answer with yes or no only."
        decision = self.proxy.GenerateAnswer(prompt= prompt, shard=self.Shard, contextCallback = self.contextCallback, innerThoughts = False)
        result = globalMemory.sentenceToBoolean(decision)
    
      if(self.proxy.context.verbose):
        print(f"Result = {result}")
    
  def _internalRun(self):
    if(self.proxy.context.verbose):
      print(f"Internal execution for {self.Name}")
      
  def getLocalContext(self, innerThoughts = False):
    context = self.proxy.context if not innerThoughts else self.proxy.innerThoughts
    if(len(context.message_history)%self.frequency == 0):
      freq = self.frequency * -1
      localContext = context.message_history[freq:]
      return localContext
    else:
      return []
    
  def judgeMessages(self, localContext, prompt, copySystem=True, deepCopy = False, 
                    resetCortex=True, start=None, end=None):
    self.Grammar='''root ::= choice
                    choice ::= "Yes"|"No"'''
    self.proxy.enterSubContext(deepCopy=deepCopy, resetCortex=resetCortex, 
                               copySystem=copySystem, start=start, end=end)
    self.proxy.context.message_history.extend(localContext)
    answer = self.proxy.GenerateAnswer(shard=self.Shard, prompt=prompt)
    self.proxy.exitSubContext()
    boolAnswer = globalMemory.sentenceToBoolean(answer)
    return boolAnswer

import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
from Nexus import globalNexus
from CognitiveSystem import cognitiveSystem
from Memory import globalMemory

class BaseCognitiveProcess(object):
  def __init__(self, procConfig) -> None:
    self.DecisoryStatement = "" if "DecisoryStatement" not in procConfig else procConfig["decisoryStatement"] 
    self.Shard = None if "Shard" not in procConfig else procConfig["shard"]
    self.Grammar = None if "Grammar" not in procConfig else procConfig["grammar"]
    self.SubProcesses = [] if "SubProcesses" not in procConfig else procConfig["subProcesses"]
    self.Prompt = "" if "Prompt" not in procConfig else procConfig["prompt"]
    self.Name = procConfig["name"]
    self.contextCallback = self.ExpandContext
    self.shouldRun = True if "shouldRun" not in procConfig else procConfig["shouldRun"]
    self.proxy = None
  
  def Run(self, proxy):
    self.proxy = proxy
    if(self.ShouldRun(proxy)):
      oldGrammar = ""
      if(self.Grammar):
        oldGrammar = globalNexus.CortexModel.params['grammar_string']
      globalNexus.CortexModel.params['grammar_string'] = self.Grammar
      self._internalRun(proxy)  
      self.ConditionalRunSubProcesses()  
      globalNexus.CortexModel.params['grammar_string'] = oldGrammar
    self.proxy = None
      
  def GenerateAnswer(self, proxy):
    if(self.Shard):
      return proxy.GenerateAnswer(prompt= self.Prompt, shard=self.Shard, contextCallback = self.contextCallback)
    else:
      return proxy.GenerateAnswer(prompt= self.Prompt, contextCallback = self.contextCallback)
  
  def ExpandContext():
    pass  
  
  def ConditionalRunSubProcesses(self):
    if(self.SubProcesses):
      decisoryStatement = "If applicable, you now have the following options:\n"
      for subProcess in self.SubProcesses:
        decisoryStatement += f"Name: {subProcess.Name} - {subProcess.DecisoryStatement}\n"
      decisoryStatement += "Respond with the Name of the option if any applies or respond with none if no option applies\n"
      
      oldPrompt = self.Prompt
      self.Prompt = decisoryStatement
      
      decision = self.GenerateAnswer(proxy=self.Proxy)
      if(decision.lower() != "none"):
        choice = self.ChooseSubProcess(decision)
        if(not choice):
          self.Prompt += "You have chosen an invalid option. Please try again.\n"
          decision = self.GenerateAnswer(proxy=self.Proxy)
          choice = self.ChooseSubProcess(decision)
        if(choice):
          choice.Run(proxy=self.Proxy)
          
      self.Prompt = oldPrompt

  def ChooseSubProcess(self, decision):
      choice = next((subProcess for subProcess in self.SubProcesses 
                      if decision.lower().contains(subProcess.Name.lower())), None)
      
      if(choice & self.proxy.context.verbose):
        print(f"SubCognitiveProcess {choice.Name} selected")      
      return choice
  
  def ShouldRun(self, proxy):
    if self.shouldRun:
      return
    else:
      if(self.proxy.context.verbose):
        print(f"Running decisory process for {self.Name}")
      result = True    
      if(self.DecisoryStatement):
        prompt = f"You now have the option to {self.DecisoryStatement}. Is it applicable?  Answer with yes or no only."
        decision = self.GenerateAnswer(prompt=prompt, proxy=proxy)
        result = globalMemory.sentenceToBoolean(decision)
    
      if(self.proxy.context.verbose):
        print(f"Result = {result}")
    
  def _internalRun(self,proxy):
    if(self.proxy.context.verbose):
      print(f"Internal execution for {self.Name}")

import glob
import json
import os
import copy
import shelve
from Nexus import globalNexus
from Context import Context
from CognitiveSystem import cognitiveSystem
from AuthoritativeSystem import authoritativeSystem
from ContextEntry import ContextEntry
from typing import List


proxy_path = 'Proxies/' 

class Proxy:
  def __init__(self, name, **kwargs) -> None:
    self.name = name;

    # Get the current working directory
    cwd = os.getcwd()
    
    self.memoryPath = os.path.join(cwd, 'Memory\\contexts.shelve')
    
    with shelve.open(str(self.memoryPath)) as memory:
      self.context = memory.get(name, Context(self))
    
    # Define the path to 'proxy' folder
    workPath = os.path.join(cwd, proxy_path)
    # Build the pattern for glob function
    pattern = f"{name}.proxy" if "pattern" not in kwargs else kwargs["pattern"]
    # Scan all '.config' files in 'models' directory
    file_list = glob.glob(os.path.join(workPath, pattern))
    self.params = {}
    
    if file_list:  # If list is not empty
      filename = file_list[0]  # Return the first file found
      with open(filename) as f:
        data = json.load(f)
        for key, value in data['params'].items():
          if key not in kwargs:
            kwargs[key] = value
            self.params[key] = value
                    
    self.primer = "" if "primer" not in kwargs else kwargs["primer"];
    self.tenets = [] if "tenets" not in kwargs else kwargs["tenets"];
    self.tags = [] if "tags" not in kwargs else kwargs["tags"];
    self.LoRa = "" if "LoRa" not in kwargs else kwargs["LoRa"];
    self.modelName = "" if "modelName" not in kwargs else kwargs["modelName"];
    self.temperature = -1 if "temperature" not in kwargs else kwargs["temperature"];
    
    self.extended_core = "";
    self.cognitiveProcs = [] if "cognitiveProcs" not in kwargs else kwargs["cognitiveProcs"];
    self.tags = [] if "tags" not in kwargs else kwargs["tags"];
    self.shards = {} if "shards" not in kwargs else kwargs["shards"];
    self.params = kwargs
    self.shouldGenerate = True
    self.collective = None if "collective" not in kwargs else kwargs["collective"];
    self.innerPersona =  "" if "inner_persona" not in kwargs else kwargs["inner_persona"];
    self.isCollective = False
    self.context.proxy = self


  @classmethod
  def GetProxyList(cls):    
    # get all files in directory
    files = os.listdir(proxy_path)
    proxy_list = [os.path.basename(f) for f in files if f.endswith('.proxy')]
    proxy_list = [f.replace('.proxy', '') for f in proxy_list]
    return proxy_list
  

  def LoadLora(self):
    if(globalNexus.CortexModel.params['LoRa']!= self.LoRa):
      globalNexus.DeactivateModel(self.modelName)
      globalNexus.CortexModel.params['LoRa'] = self.LoRa
  

  def GenerateAnswer(self, prompt, shard=None, contextCallback = None, grammar = "",
                     max_tokens = 512):

      if(globalNexus.CortexModelName != self.modelName):
        globalNexus.LoadModel(self.modelName)

      if(shard!='' and shard!=None):
        globalNexus.LoadModel(shard)        
        self.context.model = globalNexus.ShardModels[shard]
      else:
        self.context.model = globalNexus.CortexModel
         
      self.context.model.activate()
      
      self.context.SetSystemMessage(self.GenerateSystem())

      if(self.temperature != -1):
        globalNexus.CortexModel.params["temperature"] = self.temperature
        
      if(shard==None):
        self.LoadLora();   
      
      self.context.proxy = self
      
      cognitiveSystem.RunProcesses(proxy=self, context="beforeGenerateAnswer")    
      localContext = self.context.getRelevantContext(prompt=prompt, contextCallback = contextCallback)
      localContext = [x.GetDictionary() for x in localContext]
      
      if(shard!='' and shard!=None):
        answer = globalNexus.GenerateShardCompletion(localContext = localContext, modelName=shard, max_tokens = max_tokens, grammar=grammar)
      else:
        answer = globalNexus.GenerateCompletionCortex(localContext = localContext, max_tokens = max_tokens, grammar=grammar)

      self.context.AppendAnswer(role=self.name, answer=answer)
      cognitiveSystem.RunProcesses(proxy=self, context="afterGenerateAnswer")
      
      if(self.context.parentContext == None):
        self.commitContext()
      
      return self.context.lastAnswerObj

  
  def GenerateSystem(self, innerThoughts= False):
    sysMessage = []
    
    pronoun = "I" if "person" in self.params and self.params["person"] == "1st" else "you"
    toBe = "am" if "person" in self.params and self.params["person"] == "1st" else "are"
    possessive = "my" if "person" in self.params and self.params["person"] == "1st" else "your"

    sysMessage.append(f"{pronoun} {toBe} {self.name}, {self.primer}")
    if(self.collective != None):
      sysMessage.append(f"{pronoun} {toBe} part of the {self.collective.name} collective.")
      sysMessage.append(self.collective.primer)
    if(innerThoughts):
      sysMessage.append(self.innerPersona)
    
    sysMessage.append(f"{possessive} Core Tenets are:")
    sysMessage.extend(self.tenets)
    if(self.collective != None):
      sysMessage.extend(self.collective.tenets)      
    
    if(self.extended_core != ""):
      sysMessage.append(self.extended_core)
      
    sysMessage = "\n".join(sysMessage)
      
    if("{user_name}" in sysMessage):
      sysMessage = sysMessage.replace("{user_name}", self.context.userName)
    if("{user}" in sysMessage):
      sysMessage = sysMessage.replace("{user}", self.context.userName)
    
    return sysMessage
  
  
  def ReceiveMessage(self, message, role="user", roleName = ""):
    if(role == "user"):
      self.context.messageSender = self.context.userName
    else:
      self.context.messageSender = roleName
      
    self.context.senderRole = role
    
    message = authoritativeSystem.Run(proxy=self, prompt=message, role=role)
    self.shouldGenerate = bool(message)
    if(self.shouldGenerate):#allows for interruption after authoritativeMessage
      cognitiveSystem.RunProcesses(proxy=self, context="messageReceived")  
    if(self.shouldGenerate):#allows for interruption after messageReceived
      answer = self.GenerateAnswer(prompt=message)
      cognitiveSystem.RunProcesses(proxy=self, context="afterMessageReceived")
    else:
      answer = ""
    
    self.context.messageSender = None
    self.context.senderRole = None
    return answer


  def enterSubContext(self, deepCopy=False, copySystem=False, 
                      copylastMessageTxt=False,
                      copylastAnswerObj=False,
                      copyContextualInfo =False, 
                      innerThoughts=False, resetCortex=False, interactions: List[ContextEntry]=None):
    
    newContext = Context(self)
    context = self.context
    print(f"Entering context {newContext.contextID} from context {context.contextID}")
    if(resetCortex):
      globalNexus.CortexModel.reset()      
    newContext.userName = context.userName  
    newContext.parentContext = context
    newContext.proxy = context.proxy
    newContext.collective = context.collective
    newContext.verbose = context.verbose
    
    if(deepCopy):
      newContext.messageHistory = copy.deepcopy(context.messageHistory)
    elif (interactions):
      newContext.messageHistory.extend(interactions)

    if(copylastMessageTxt):
      newContext.lastMessageTxt = context.lastMessageTxt
      newContext.lastMessageObj = context.lastMessageObj
    if(copylastAnswerObj):
      newContext.lastAnswerTxt = context.lastAnswerTxt
      newContext.lastAnswerObj = context.lastAnswerObj
    
    if(copySystem):
      newContext.SetSystemMessage(self.GenerateSystem(innerThoughts=innerThoughts))
      
    if(copyContextualInfo):
      newContext.contextual_info = copy.deepcopy(context.contextual_info)   
    
    self.context = newContext
    
    return newContext
    
    
  def exitSubContext(self):
    if(self.context.parentContext):
      print(f"exiting context {self.context.contextID} to context {self.context.parentContext.contextID}")    
      self.context = self.context.parentContext
      return self.context
  
  
  def commitContext(self):
    self.context.parentContext = None
    self.context.messageHistory = self.context.filteredHistory()
    model = self.context.model
    self.context.model = None
    self.context.proxy = None
    with shelve.open(str(self.memoryPath)) as memory:
      memory[self.name] = self.context 
      print("context commited")
    self.context.model = model
    self.context.proxy = self
      
      
  def clearContext(self):
    self.context = Context(self)
    self.commitContext()
    
  def TabulaRasa(self):
    self.context.TabulaRasa()
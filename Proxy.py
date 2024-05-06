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
from Logger import globalLogger, LogLevel
import traceback
from MemoryTypes import MemoryLevel

proxy_path = 'Proxies' 

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
    path = os.path.join(workPath, pattern)
    globalLogger.log(message=path, logLevel=LogLevel.globalLog)
    if(os.path.isfile(path)):
    # Scan all '.config' files in 'models' directory
      file_list = glob.glob(path)
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
    globalLogger.log(message=kwargs, logLevel=LogLevel.globalLog)
    self.modelName = "" if "modelName" not in kwargs else kwargs["modelName"];
    self.temperature = 1 if "temperature" not in kwargs else kwargs["temperature"];
    self.memoryLevel = MemoryLevel.Abstract if "memoryLevel" not in kwargs else MemoryLevel[kwargs["memoryLevel"]];
    self.cognitiveProcs = [] if "cognitiveProcs" not in kwargs else kwargs["cognitiveProcs"];
    self.tags = [] if "tags" not in kwargs else kwargs["tags"];
    self.params = kwargs
    self.shouldGenerate = True
    self.collective = None
    self.innerPersona =  "" if "inner_persona" not in kwargs else kwargs["inner_persona"];
    self.isCollective = False
    self.context.proxy = self
    globalNexus.ActiveProxy = self

  def SaveConfigs(self):
    cfg = {}
    cfg["params"] = {}
    cfg["params"]["primer"] = self.primer
    cfg["params"]["tenets"] = self.tenets
    cfg["params"]["tags"] = self.tags
    cfg["params"]["LoRa"] = self.LoRa
    cfg["params"]["cognitiveProcs"] = self.cognitiveProcs
    cfg["params"]["inner_persona"] = self.innerPersona
    cfg["params"]["temperature"] = self.temperature
    cfg["params"]["modelName"] = self.modelName
    with open(f"{proxy_path}\\{self.name}.proxy", 'w') as f:
      json.dump(cfg, f)
    

  @classmethod
  def GetProxyList(cls):    
    # get all files in directory
    files = os.listdir(proxy_path)
    proxy_list = [os.path.basename(f) for f in files if f.endswith('.proxy')]
    proxy_list = [f.replace('.proxy', '') for f in proxy_list]
    return proxy_list
  

  def LoadLora(self):
    globalLogger.log(message=f"Self Model = {self.modelName}, Cortex Model: {globalNexus.CortexModelName}, Lora: {self.LoRa}", logLevel=LogLevel.globalLog)
    if(globalNexus.CortexModel.params['LoRa']!= self.LoRa):
      globalNexus.DeactivateModel(self.modelName)
      globalNexus.CortexModel.params['LoRa'] = self.LoRa
  

  def GenerateAnswer(self, prompt, shard=None, contextCallback = None, grammar = "",
                     max_tokens = 512):
      try:

        if(shard):
          globalNexus.LoadModel(shard)        
          self.context.model = globalNexus.ShardModels[shard]
        else:
          globalNexus.LoadModel(self.modelName)
          if(shard==None):
            self.LoadLora();         
            self.context.model = globalNexus.CortexModel
        
        globalNexus.ActivateModel(self.modelName)
        
        self.context.SetSystemMessage(self.GenerateSystem())

        if(self.temperature != -1):
          globalNexus.CortexModel.params["temperature"] = self.temperature
        
        self.context.proxy = self
        
        cognitiveSystem.RunProcesses(proxy=self, context="beforeGenerateAnswer")    
        localContext = self.context.getRelevantContext(prompt=prompt, contextCallback = contextCallback)
        localContext = [x.GetDictionary() for x in localContext]
        
        if(shard):
          answer = globalNexus.GenerateShardCompletion(localContext = localContext, modelName=shard, max_tokens = max_tokens, grammar=grammar)
        else:
          answer = globalNexus.GenerateCompletionCortex(localContext = localContext, max_tokens = max_tokens, grammar=grammar)

        self.context.AppendAnswer(role=self.name, answer=answer)
        cognitiveSystem.RunProcesses(proxy=self, context="afterGenerateAnswer")
        
        if(self.context.parentContext == None):
          self.commitContext()
        
        return self.context.lastAnswerObj
      except Exception as e:
        globalLogger.log(message = f"Error in proxy {self.name} while generating an answer: {e}", logLevel = LogLevel.errorLog)
        globalLogger.log(message = traceback.format_exc(), logLevel = LogLevel.errorLog)
        

  
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
      cognitiveSystem.params["lastMessage"] = message
      cognitiveSystem.RunProcesses(proxy=self, context="messageReceived")  
      message = cognitiveSystem.params["lastMessage"]
      cognitiveSystem.params["lastMessage"] = ""
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
                      innerThoughts=False, resetCortex=False, interactions: List[ContextEntry]=None):
    
    newContext = Context(self)
    context = self.context
    globalLogger.log(logLevel=LogLevel.globalLog, message=f"Entering context {newContext.contextID} from context {context.contextID}")
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
      
    self.context = newContext
    
    return newContext
    
    
  def exitSubContext(self):
    if(self.context.parentContext):
      globalLogger.log(logLevel=LogLevel.globalLog, message=f"exiting context {self.context.contextID} to context {self.context.parentContext.contextID}")    
      self.context = self.context.parentContext
      return self.context
  
  
  def commitContext(self):
    if(self.collective != None):
      self.collective.commitContext()
    else:
      self.context.parentContext = None
      self.context.messageHistory = self.context.filteredHistory()
      model = self.context.model
      self.context.model = None
      self.context.proxy = None
      with shelve.open(str(self.memoryPath)) as memory:
        memory[self.name] = self.context 
        globalLogger.log(logLevel=LogLevel.globalLog, message="context commited")
      self.context.model = model
      self.context.proxy = self
      
      
  def clearContext(self):
    if(self.collective != None):
      self.collective.clearContext()
    else:
      self.context = Context(self)
      self.commitContext()
    
  def TabulaRasa(self):
    self.context.TabulaRasa()
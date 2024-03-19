import glob
import json
import os
import copy
import shelve

from Nexus import globalNexus
from Context import Context
from CognitiveSystem import cognitiveSystem
from Memory import globalMemory
from AuthoritativeSystem import authoritativeSystem

proxy_path = 'Proxies/' 

class Proxy:
  def __init__(self, name, **kwargs) -> None:
    self.name = name;

    # Get the current working directory
    cwd = os.getcwd()
    
    self.memoryPath = os.path.join(cwd, 'Memory\\contexts.shelve')
    
    with shelve.open(str(self.memoryPath)) as memory:
      self.context = memory.get(name, Context())
      self.context.sessionStart = None
      self.innerThoughts = memory.get(name+".inner", Context())
      self.innerThoughts.sessionStart = None
    
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
    self.coreStatements = [] if "coreStatements" not in kwargs else kwargs["coreStatements"];
    self.tags = [] if "tags" not in kwargs else kwargs["tags"];
    self.LoRa = "" if "LoRa" not in kwargs else kwargs["LoRa"];
    self.model_name = "" if "model_name" not in kwargs else kwargs["model_name"];
    self.temperature = -1 if "temperature" not in kwargs else kwargs["temperature"];
    
    self.extended_core = "";
    self.cognitiveProcs = [] if "cognitiveProcs" not in kwargs else kwargs["cognitiveProcs"];
    self.tags = [] if "tags" not in kwargs else kwargs["tags"];
    self.shards = {} if "shards" not in kwargs else kwargs["shards"];
    self.params = kwargs
    self.shouldGenerate = True
    self.collective = None if "collective" not in kwargs else kwargs["collective"];
    self.context.systemMessage = self.GenerateSystem()
    self.innerPersona =  "" if "inner_persona" not in kwargs else kwargs["inner_persona"];
    self.innerThoughts.systemMessage = self.GenerateSystem(innerThoughts = True)
    self.isCollective = False

  @classmethod
  def get_proxy_list(cls):    
    # get all files in directory
    files = os.listdir(proxy_path)
    proxy_list = [os.path.basename(f) for f in files if f.endswith('.proxy')]
    proxy_list = [f.replace('.proxy', '') for f in proxy_list]
    return proxy_list
  
  def LoadLora(self):
    if(globalNexus.CortexModel.params['LoRa']!= self.LoRa):
      globalNexus.deactivate_model(self.model_name)
      globalNexus.CortexModel.params['LoRa'] = self.LoRa
  
  def GenerateAnswer(self, prompt, shard=None, contextCallback = None, innerThoughts = False, grammar = "",
                     max_tokens = 0, recusiveLevel = 0):
      if(innerThoughts):
        context = self.innerThoughts
      else:
        context = self.context
      
      oldModel = context.model

      if(globalNexus.CortexModel_name != self.model_name):
        globalNexus.load_model(self.model_name)

      if(shard!='' and shard!=None):
        context.model = globalNexus.ShardModels[shard]
      else:
        context.model = globalNexus.CortexModel        
        globalNexus.load_grammar(grammar)

      if(self.temperature != -1):
        globalNexus.CortexModel.params["temperature"] = self.temperature
        
      if(shard==None):
        self.LoadLora();   
        
      context.model.activate()
      context.window_size = globalNexus.CortexModel.params["n_ctx"] - globalNexus.CortexModel.params["max_tokens"]      
      context.proxy = self
      cognitiveSystem.RunProcesses(proxy=self, context="beforeGenerateAnswer")    
      localContext = context.get_relevant_context(prompt=prompt, contextCallback = contextCallback)
        
      if(shard!='' and shard!=None):
        answer = globalNexus.generate_completion_shard(localContext = localContext, model_name=shard, max_tokens = max_tokens)
      else:
        answer = globalNexus.generate_completion_cortex(localContext = localContext, max_tokens = max_tokens)
      
      context.contextual_info = None
      context.append_answer(role=self.name, message=answer)
      cognitiveSystem.RunProcesses(proxy=self, context="afterGenerateAnswer")
      
      if(not context.last_answer) or (context.last_answer == " " or context.last_answer == ""):
        print(f"Removing last answer and trying again. Reason: empty answer")
        if(recusiveLevel < 1):
          self.enterSubContext(deepCopy=True)
          prompt = prompt + f" You gave me an empty answer! Please try again! Answer the following: {prompt}\n"
          print(f"Trying to get a non empty message by asking the model explicitly. Reason: empty answer")          
          subContextAnswer = self.GenerateAnswer(prompt=prompt, shard=shard, contextCallback = contextCallback, max_tokens=max_tokens, recusiveLevel = recusiveLevel+1)
          self.exitSubContext()          
          self.context.last_answer = subContextAnswer
      
      context.model = oldModel
      self.commitContext()
      return context.last_answer
  
  def GenerateSystem(self, innerThoughts= False):
    sysMessage = []
    
    pronoun = "I" if "person" in self.params and self.params["person"] == "1st" else "you"
    toBe = "am" if "person" in self.params and self.params["person"] == "1st" else "are"

    sysMessage.append(f"{pronoun} {toBe} {self.name}, {self.primer}")
    if(self.collective != None):
      sysMessage.append(f"{pronoun} {toBe} part of the {self.collective.name} collective.")
      sysMessage.append(self.collective.primer)
    if(innerThoughts):
      sysMessage.append(self.innerPersona)
    else:
      sysMessage.append(f"{pronoun} believe, above all, in the following:")
      sysMessage.extend(self.coreStatements)
      if(self.collective != None):
        sysMessage.extend(self.collective.coreStatements)      
      if(self.extended_core != ""):
        sysMessage.append(self.extended_core)
    sysMessage = "\n".join(sysMessage)
      
    if("{user_name}" in sysMessage):
      sysMessage = sysMessage.replace("{user_name}", self.context.userName)
    if("{user}" in sysMessage):
      sysMessage = sysMessage.replace("{user}", self.context.userName)
   
    
    return sysMessage
  
  
  def MessageProxy(self, proxy_name, message):
    cognitiveSystem.RunProcesses(proxy=self, context="beforeMessageProxy")
    if(self.collective != None) & (proxy_name in self.collective.proxies):
      self.collective.proxies[proxy_name].ReceiveMessage(poxy=self, message=message)
  
  def MessageColective(self, message):
    #####################################################################################################
    cognitiveSystem.RunProcesses(proxy=self, context="beforeMessageCollective")
    pass
  
  def ReceiveMessage(self, message, role="user"):
    self.context.messageSender = self.context.userName
    self.context.senderRole = role
    self.shouldGenerate = True
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
                      copyLastMessage=False,
                      copyLastAnswer=False,
                      copyContextualInfo =False, 
                      innerThoughts=False, resetCortex=False, start = None, end = None):
    
    newContext = Context()
    if(resetCortex):globalNexus.CortexModel.reset()
    context = self.innerThoughts if innerThoughts else self.context
    print(f"Entering context {newContext.contextID} from context {context.contextID}")
    newContext.userName = context.userName  
    newContext.parentContext = context
    newContext.proxy = context.proxy
    newContext.collective = context.collective
    newContext.verbose = context.verbose
    
    if(deepCopy):
      newContext.message_history = copy.deepcopy(context.message_history)
    elif (start or end):
      newContext.message_history = context.get_relevant_context(start=start, end=end)

    if(copyLastMessage):
      newContext.last_message = context.last_message
      newContext.append_message(context.last_message, role="user")
    if(copyLastAnswer):
      newContext.last_answer = context.last_answer
      newContext.append_message(context.last_answer, role="assistant")
    
    if(copySystem):
      newContext.systemMessage = context.systemMessage
      
    if(copyContextualInfo):
      newContext.contextual_info = copy.deepcopy(context.contextual_info)   
    
    
    if(innerThoughts):
      self.innerThoughts = newContext
    else:
      self.context = newContext
    
    return newContext
    
  def exitSubContext(self, innerThoughts=False):
    context = self.innerThoughts if innerThoughts else self.context
    if(context.parentContext):
      print(f"exiting context {self.context.contextID} to context {self.context.parentContext.contextID}")    
      if(innerThoughts):
        self.innerThoughts = context.parentContext
      else:
        self.context = context.parentContext
      return context
  
  def commitContext(self):
    with shelve.open(str(self.memoryPath)) as memory:
      memory[self.name] = self.context 
      memory[self.name+".inner"] = self.innerThoughts 
      print("context commited")
      
  def clearContext(self):
    self.context = Context()
    self.innerThoughts = Context()
    self.commitContext()
    
  
  def deactivateCortex(self):
    globalNexus.CortexModel.deactivate()
    
  def activateCortex(self):
    globalNexus.CortexModel.activate()
import glob
import json
import os
import copy

from Nexus import globalNexus
from Context import Context
from CognitiveSystem import cognitiveSystem
from Memory import globalMemory


proxy_path = 'Proxies/' 

class Proxy:
  def __init__(self, name, **kwargs) -> None:
    self.name = name;
    self.context = Context()
    self.innerThoughts = Context()
    
    # Get the current working directory
    cwd = os.getcwd()
    # Define the path to 'proxy' folder
    workPath = os.path.join(cwd, proxy_path)
    # Build the pattern for glob function
    pattern = f"{name}.proxy"
    # Scan all '.config' files in 'models' directory
    file_list = glob.glob(os.path.join(workPath, pattern))
    
    if file_list:  # If list is not empty
      filename = file_list[0]  # Return the first file found
      with open(filename) as f:
        data = json.load(f)
        for key, value in data['params'].items():
          if key not in kwargs:
            kwargs[key] = value
                    
    self.primer = "" if "primer" not in kwargs else kwargs["primer"];
    self.coreStatements = [] if "coreStatements" not in kwargs else kwargs["coreStatements"];
    self.LoRa = "" if "LoRa" not in kwargs else kwargs["LoRa"];
    self.model_name = "" if "model_name" not in kwargs else kwargs["model_name"];
    globalNexus.load_model(self.model_name)
    self.extended_core = "";
    self.cognitiveProcs = [] if "cognitiveProcs" not in kwargs else kwargs["cognitiveProcs"];
    cognitiveSystem.RegisterCommonProcesses(self)
    self.shards = {} if "shards" not in kwargs else kwargs["shards"];
    self.memory = None
    self.params = kwargs
    self.shouldGenerate = True
    self.collective = None    
    self.context.systemMessage = self.GenerateSystem()
    self.innerPersona =  "" if "inner_persona" not in kwargs else kwargs["inner_persona"];
    self.innerThoughts.systemMessage = self.GenerateSystem(innerThoughts = True)

  @classmethod
  def get_proxy_list(cls):    
    # get all files in directory
    files = os.listdir(proxy_path)
    proxy_list = [os.path.basename(f) for f in files if f.endswith('.proxy')]
    proxy_list = [f.replace('.proxy', '') for f in proxy_list]
    return proxy_list
  
  def GenerateAnswer(self, prompt, shard=None, contextCallback = None, innerThoughts = False):
      if(innerThoughts):
        context = self.innerThoughts
      else:
        context = self.context
      
      oldModel = context.model
      if(shard!='' and shard!=None):
        context.model = globalNexus.ShardModels[shard]
      else:
        context.model = globalNexus.CortexModel        

      context.model.activate()
      context.window_size = globalNexus.CortexModel.params["n_ctx"] - globalNexus.CortexModel.params["max_tokens"]      
      context.proxy = self
      cognitiveSystem.RunProcesses(proxy=self, context="beforeGenerateAnswer")    
      localContext = context.get_relevant_context(prompt=prompt, contextCallback = contextCallback)
      
      if(self.LoRa):
        self.LoadLora();      
        
      if(shard!='' and shard!=None):
        answer = globalNexus.generate_completion_shard(localContext = localContext, model_name=shard)
      else:
        answer = globalNexus.generate_completion_cortex(localContext = localContext)
      
      if(self.LoRa):
        self.UnloadLora();
      
      context.contextual_info = None
      context.append_message_object(role=self.name, message=answer)
      cognitiveSystem.RunProcesses(proxy=self, context="afterGenerateAnswer")
      
      if(not context.last_answer):
        context.remove_last_pair()
        if(context.verbose):
          print(f"Removing last answer and trying again. Reason: empty answer")
        self.GenerateAnswer(prompt=prompt, shard=shard, contextCallback = contextCallback)
      
      context.model = oldModel
      return context.last_answer
  
  def GenerateSystem(self, innerThoughts= False):
    sysMessage = []
    sysMessage.append(f"You are {self.name}, {self.primer}")
    if(innerThoughts):
      sysMessage.append(self.innerPersona)
    else:
      sysMessage.extend(self.coreStatements)
      if(self.extended_core != ""):
        sysMessage.append(self.extended_core)
    sysMessage = "\n".join(sysMessage)
      
    if("{user_name}" in sysMessage):
      sysMessage = sysMessage.replace("{user_name}", self.context.userName)
    if("{user}" in sysMessage):
      sysMessage = sysMessage.replace("{user}", self.context.userName)
    
    return sysMessage
  
  def GetDecisoryStatement(self):
    return f"{self.name}, {self.primer}"
  
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

    if(message.startswith("/")):
      self.context.last_message = message
      self.shouldGenerate = False #stopr generation for authoritative messages. 
      #Authoritative processes may set this back to true to proceed with normal generation
      cognitiveSystem.RunProcesses(proxy=self, context="authoritativeMessage")        
    
    if(self.shouldGenerate):
      cognitiveSystem.RunProcesses(proxy=self, context="messageReceived")  
      answer = self.GenerateAnswer(prompt=message)
      cognitiveSystem.RunProcesses(proxy=self, context="afterMessageReceived")
    
    self.context.messageSender = None
    self.context.senderRole = None
    return answer
        
              
  def ShouldAnswer(self, message, proxy, collective)-> bool:
    lastAnswer = self.context.message_history[-1]
    lastMessage = self.context.last_message    
    if(proxy):
      sender = proxy.name
    elif(collective):
      sender = collective.name
    else:
      sender = "user"    
    self.enterSubContext()
    
    if(lastAnswer["content"] != lastMessage):
      if(sender == "user"):
        self.context.append_message(message=lastAnswer["context"], role=lastAnswer["role"])
        self.context.append_message(message=lastMessage, role=sender)
      else:
        self.context.append_message(message=lastMessage, role=sender)
        self.context.append_message(message=lastAnswer["context"], role=lastAnswer["role"])
    else:
        self.context.append_message(message=lastAnswer["context"], role=lastAnswer["role"])

    prompt = f"You have received the following message: {message}, sent by {sender}. Given this brief context and what you know about yourself, are you qualified to answer? Respond with yes or no only"
    
    result = False;
    
    #if there are any cog procs registered to should answer
    if(cognitiveSystem.RunProcesses(proxy=self, context="shouldAnswer")):
      decision = self.context.last_answer
      #shouldAnswer cog proc must pump the last answer up to the parent
    else:
      decision = self.GenerateAnswer(prompt=prompt)    
      
    decision = str(decision).lower()
    result = globalMemory.sentenceToBoolean(decision)
    
    self.exitSubContext()
    
    return result;
  
  def LoadLora(self):
    pass
  
  def UnloadLora(self):
    pass
  def enterSubContext(self, deepCopy=False, copySystem=False, copyLastMessage=False,copyLastAnswer=False,
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
  
  def deactivateCortex(self):
    globalNexus.CortexModel.deactivate()
    
  def activateCortex(self):
    globalNexus.CortexModel.activate()
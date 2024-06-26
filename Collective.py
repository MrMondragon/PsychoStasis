from Proxy import Proxy
from Nexus import globalNexus
from AuthoritativeSystem import authoritativeSystem
from CognitiveSystem import cognitiveSystem
from Logger import globalLogger, LogLevel
import os

proxy_path = 'Proxies/' 

class Collective(Proxy):

  def __init__(self, name, **kwargs) -> None:
    super().__init__(name,  pattern = f"{name}.collective")
    proxies = [] if "proxies" not in self.params else self.params["proxies"]
    self.activeSpeaker = None
    self.proxies = {}
    if(proxies):
      for proxy in proxies:
        globalLogger.log(logLevel=LogLevel.globalLog, message=f"Loading proxy: {proxy}")
        
        self.proxies[proxy] = Proxy(proxy, collective=self)
        self.proxies[proxy].collective = self;
        self.proxies[proxy].context = self.context;

        
    
    proxy = proxies[0] 
    self.activeSpeaker = self.proxies[proxy]
    globalNexus.ActiveProxy = self.proxies[proxy]
    globalLogger.log(logLevel=LogLevel.globalLog, message=f"Active Speaker: {proxy}")
        
    self.lastSpeaker = None
    self.isCollective = True
    self.sysMessage = self.GenerateSystem()
    globalNexus.ActiveCollective = self
  
    
    
    
      
  @classmethod
  def GetCollectiveList(cls):    
    # get all files in directory
    files = os.listdir(proxy_path)
    collective_list = [os.path.basename(f) for f in files if f.endswith('.collective')]
    collective_list = [f.replace('.collective', '') for f in collective_list]
    return collective_list
    
  def SwitchToSpeaker(self, name):
    self.lastSpeaker = self.activeSpeaker
    self.activeSpeaker = self.proxies[name]
  
  def SwitchToAny(self, prompt): 
    minDistance = float('inf')
    nextSpeaker = None
    for name, proxy in self.proxies.items():
      for tag in proxy.tags:
        distance = globalNexus.ComputeSimilarity(prompt, tag)
        if(distance<minDistance):
          minDistance = distance
          nextSpeaker = name
    self.SwitchToSpeaker(nextSpeaker)      
    
  
  def All(self, prompt):
    for name, proxy in self.proxies.items():
      self.SwitchToSpeaker(name)
      proxy.ReceiveMessage(message=prompt)
      answer = proxy.ReceiveMessage(message=prompt)
      globalLogger.log(logLevel=LogLevel.globalLog, message=f"{self.activeSpeaker.name}: {answer}")  
      
      
  def Others(self, prompt):
    for name, proxy in self.proxies.items():
      if(proxy != self.activeSpeaker):
        self.SwitchToSpeaker(name)
        answer = proxy.ReceiveMessage(message=prompt)
        globalLogger.log(logLevel=LogLevel.globalLog, message=f"{self.activeSpeaker.name}: {answer}")
        
  
  def ReceiveMessage(self, message, role="user", roleName = ""):
    sysMessage = self.sysMessage

    if("{proxy_name}" in sysMessage):
        sysMessage = sysMessage.replace("{proxy_name}", self.activeSpeaker.name)   
    if("{collective_members|proxy_name}" in sysMessage):
      proxyList = self.proxies.keys()
      proxyList = filter(lambda x: x != self.activeSpeaker.name, proxyList)
      sysMessage = sysMessage.replace("{collective_members|proxy_name}", ", ".join(proxyList))
        
    self.context.systemMessage = sysMessage    
    answer = None
    self.shouldGenerate = True    
    message = authoritativeSystem.Run(proxy=self, prompt=message, role=role)
    self.shouldGenerate = bool(message)
    if(self.shouldGenerate):#allows for interruption after authoritativeMessage
      cognitiveSystem.RunProcesses(proxy=self, context="collectiveMessageReceived")
    if(self.shouldGenerate):#allows for interruption after collectiveMessageReceived
      answer = self.activeSpeaker.ReceiveMessage(message=message, role=role, roleName = roleName)
      cognitiveSystem.RunProcesses(proxy=self, context="afterCollectiveMessageReceived")
    self.context.messageSender = None
    self.context.senderRole = None
    
    if(not answer):
      answer = self.context.lastAnswerObj
      
    return answer

  def setProxyContexts(self):
    for proxy in self.proxies.values():
      proxy.context = self.context

    
  def clearContext(self):
    super().clearContext()
    self.setProxyContexts()
      
  def enterSubContext(self, deepCopy=False, copySystem=False, 
                      copylastMessageTxt=False,
                      copylastAnswerObj=False,
                      copyContextualInfo =False, 
                      innerThoughts=False, resetCortex=False, interactions =None):
    super().enterSubContext(deepCopy=deepCopy, copySystem=copySystem,
                            copylastMessageTxt=copylastMessageTxt,
                            copylastAnswerObj=copylastAnswerObj,
                            copyContextualInfo =copyContextualInfo,
                            innerThoughts=innerThoughts, resetCortex=resetCortex, interactions=interactions)
    self.setProxyContexts()
      
  def exitSubContext(self):
    super().exitSubContext()
    self.setProxyContexts()
    
  def invite(self, proxyName):
    newProxy = Proxy(proxyName, collective=self)
    self.proxies[proxyName] = newProxy
    newProxy.context = self.context

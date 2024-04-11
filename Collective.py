from Proxy import Proxy
from Nexus import globalNexus
from AuthoritativeSystem import authoritativeSystem
from CognitiveSystem import cognitiveSystem

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
        print(f"Loading proxy: {proxy}")
        self.proxies[proxy] = Proxy(proxy, collective=self)
        self.proxies[proxy].collective = self;
        self.proxies[proxy].context = self.context;
        if(self.activeSpeaker == None):
          print(f"Active Speaker: {proxy}")
          self.activeSpeaker = self.proxies[proxy]
        
    self.lastSpeaker = None
    self.isCollective = True
    self.sysMessage = self.GenerateSystem()
    
    
      
  @classmethod
  def get_collective_list(cls):    
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
        distance = globalNexus.compute_similarity(prompt, tag)
        if(distance<minDistance):
          minDistance = distance
          nextSpeaker = name
    self.SwitchToSpeaker(nextSpeaker)      
    
  
  def All(self, prompt):
    for name, proxy in self.proxies.items():
      self.SwitchToSpeaker(name)
      proxy.ReceiveMessage(message=prompt)
  
  def Others(self, prompt):
    for name, proxy in self.proxies.items():
      if(proxy != self.activeSpeaker):
        self.SwitchToSpeaker(name)
        proxy.ReceiveMessage(message=prompt)
        
  def ReceiveMessage(self, message, role="user"):

    sysMessage = self.sysMessage
    
    if("{proxy_name}" in sysMessage):
        sysMessage = sysMessage.replace("{proxy_name}", self.activeSpeaker.name)   
    if("{collective_members|proxy_name}" in sysMessage):
      proxyList = self.proxies.keys()
      proxyList = filter(lambda x: x != self.activeSpeaker.name, proxyList)
      sysMessage = sysMessage.replace("{collective_members|proxy_name}", ", ".join(proxyList))
        
    self.context.systemMessage = sysMessage    
    
    self.shouldGenerate = True    
    message = authoritativeSystem.Run(proxy=self, prompt=message, role=role)
    self.shouldGenerate = bool(message)
    if(self.shouldGenerate):#allows for interruption after authoritativeMessage
      cognitiveSystem.RunProcesses(proxy=self, context="collectiveMessageReceived")
    if(self.shouldGenerate):#allows for interruption after collectiveMessageReceived
      answer = self.activeSpeaker.ReceiveMessage(message=message, role=role)
      cognitiveSystem.RunProcesses(proxy=self, context="afterCollectiveMessageReceived")
    self.context.messageSender = None
    self.context.senderRole = None
    return answer
    


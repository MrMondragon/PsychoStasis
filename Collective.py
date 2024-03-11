from Proxy import Proxy
from Nexus import globalNexus
from AuthoritativeSystem import authoritativeSystem
from CognitiveSystem import cognitiveSystem

import os

proxy_path = 'Proxies/' 

class Collective(Proxy):

  def __init__(self, name, **kwargs) -> None:
    super().__init__(name,  pattern = f"{name}.collective")
    proxies = [] if "proxies" not in kwargs else kwargs["proxies"]
    self.proxies = {}
    if(proxies):
      for proxy in proxies:
        self.proxies[proxy] = Proxy(proxy, collective=self)
        self.proxies[proxy].collective = self;
        self.proxies[proxy].context = self.context;
    self.lastSpeaker = None
    self.activeSpeaker = None
    self.isCollective = True
    
    
      
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
    self.context.messageSender = self.context.userName
    self.context.senderRole = role
    self.shouldGenerate = True    
    message = authoritativeSystem.Run(proxy=self, prompt=message, role=role)
    self.shouldGenerate = bool(message)
    if(self.shouldGenerate):#allows for interruption after authoritativeMessage
      cognitiveSystem.RunProcesses(proxy=self, context="collectiveMessageReceived")
    if(self.shouldGenerate):#allows for interruption after collectiveMessageReceived
      answer = self.activeSpeaker.GenerateAnswer(prompt=message)
      cognitiveSystem.RunProcesses(proxy=self, context="afterCollectiveMessageReceived")
    self.context.messageSender = None
    self.context.senderRole = None
    return answer
    
      
      
      
      
  # @name - switch active speaker to @name
  # @any - switch active speaker to closest vectorial distance based on tags
  # no @ - active speaker
  # @name + no message - forwards the previous message to @name
  # @all - all proxies in collective in order of vectorial distance
  # << + no message - remove last message
  # >> + no message - regenerate last message
  # <<<< + no message - remove last message pair
  # cognitive process to feed relationships between proxies
  #     "based on the conversation so far, what is your opinion about @name"
  #     triggered when the speaker changes and asked about last speaker
  # decisory statements and other prompts generated within subcontexts should be fed to innerThoughts
  
  # All contexts should be updated
  # The collective can assign its own context to each proxy and manage system prompts on message received
  #     because cogsys prompts are assigned after message received
  # Right now, there's no mechanic in place to allow for two proxies to call each other
  
  # cogProc to assign and update extended core. if there's no extended core, the proxy should check his memory for 
  
  #     but this can be implemented via cogProcess
  # ^^N^^L - shift message up -- useful when asking the opinion of multiple proxies on a subject
  #          N = N messages to shift
  #          L = L lines to shift up
  # vvKvvN - shift message down -- useful when returning to a topic
  #          N = N messages to shift
  #          K = K lines above the last
  #          Messages shifted down always go to the bottom
  # shorter versions like ^^N and vvK can be used as well  
  # authoritative modules that register the class name, the function and the regex pattern for dynamic calling
  #     maybe registered and managed by a new class instead of cogniteveSystem
  
  
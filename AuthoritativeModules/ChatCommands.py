import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
from AuthoritativeSystem import authoritativeSystem
import re

class ChatCommands(object):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
  
  def RegisterCommands(self):
    authoritativeSystem.Commands["<<"] = tuple(func = self.removeLast, descriptrion = "remove last context message")
    authoritativeSystem.Commands[r"@\d+"] = tuple(func = self.at, descriptrion = "switch to speaker. @name, @all, @others, @any")
    authoritativeSystem.Commands[r"/\^\d+(\^\d+)?"] = tuple(func = self.switchUp, descriptrion = "switch up context")
    authoritativeSystem.Commands[r"/v\d+(v\d+)?"] = tuple(func = self.switchDown, descriptrion = "switch down context")
    
  
  def removeLast(self, prompt, command, proxy):
    if(command.startswith("<<<<")):
      proxy.context.remove_last_pair()
    elif (command.startswith("<<")):
      proxy.context.remove_last()      
    proxy.shouldGenerate = False
    return ""
    
  def at(self, prompt, command, proxy):
    atProxy = command
    prompt = prompt.replace(atProxy, "")
    prompt = prompt.strip()
    atProxy = atProxy.lower().strip("@")    
    if(atProxy == "any"):
      proxy.SwitchToAny(prompt)
    elif(atProxy == "all"):
      proxy.All()
      return ""
    elif(atProxy == "others"):
      proxy.Others()
      return ""
    else:
      proxy.SwitchToSpeaker(atProxy)
    return prompt
  
  def switchUp(self, prompt, command, proxy):
    nl = re.findall(r"\d+", command)
    n = int(nl[0])
    if(len(nl) > 1):
      l = int(nl[1])
    else:
      l = 1
    proxy.context.switchUp(n, l)
    return ""
  
  def switchDown(self, prompt, command, proxy):
    nl = re.findall(r"\d+", command)
    n = int(nl[0])
    if(len(nl) > 1):
      l = int(nl[1])
    else:
      l = 1
    proxy.context.switchDown(n, l)
    return ""
    
    
import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
import re
from _Command import _Command
from Logger import globalLogger

class ChatCommands(object):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
  
  def RegisterCommands(self, authoritativeSystem):
    authoritativeSystem.Commands["<<"] = _Command(func = self.removeLast, description = "remove last context message")
    authoritativeSystem.Commands[r"@\w+"] = _Command(func = self.at, description = "switch to speaker. @name, @all, @others, @any")
    authoritativeSystem.Commands[r"/A\d+(A\d+)?"] = _Command(func = self.SwitchUp, description = "switch up context")
    authoritativeSystem.Commands[r"/V\d+(V\d+)?"] = _Command(func = self.SwitchDown, description = "switch down context")
    authoritativeSystem.Commands[r"/new"] = _Command(func = self.newContext, description = "start a new context")
    
  
  def removeLast(self, prompt, command, proxy):
    globalLogger.log(f"removing last message: {prompt}")
    if(prompt.startswith("<<<<")):
      proxy.context.RemoveLast() 
      proxy.context.RemoveLast() 
      globalLogger.log("last 2 messages removed")
    elif (prompt.startswith("<<")):
      proxy.context.RemoveLast() 
      globalLogger.log("last message removed")
    proxy.commitContext()     
    proxy.shouldGenerate = False
    return ""
    
  def at(self, prompt, command, proxy):
    atProxy = command
    prompt = prompt.replace(atProxy, "")
    prompt = prompt.strip()
    atProxy = atProxy.strip("@")    
    if(atProxy.lower() == "any"):
      proxy.SwitchToAny(prompt)
    elif(atProxy.lower() == "all"):
      proxy.All()
      return ""
    elif(atProxy.lower() == "others"):
      proxy.Others()
      return ""
    else:
      proxy.SwitchToSpeaker(atProxy)
      prompt = atProxy + " " + prompt
    return prompt
  
  def SwitchUp(self, prompt, command, proxy):
    nl = re.findall(r"\d+", command)
    n = int(nl[0])
    if(len(nl) > 1):
      l = int(nl[1])
    else:
      l = 1
    proxy.context.SwitchUp(n, l)
    return ""
  
  def SwitchDown(self, prompt, command, proxy):
    nl = re.findall(r"\d+", command)
    n = int(nl[0])
    if(len(nl) > 1):
      l = int(nl[1])
    else:
      l = 1
    proxy.context.SwitchDown(n, l)
    return ""
  
  def newContext(self, prompt, command, proxy):
    proxy.clearContext()
    
    
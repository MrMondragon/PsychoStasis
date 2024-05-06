import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
import re
from _Command import _Command
from Logger import globalLogger, LogLevel

class ChatCommands(object):
  def __init__(self, **kwargs):
    pass
  
  def RegisterCommands(self, authoritativeSystem):
    authoritativeSystem.Commands["<<"] = _Command(func = self.removeLast, description = "remove last context message")
    authoritativeSystem.Commands[">>"] = _Command(func = self.regen, description = "regenerate last answer")
    authoritativeSystem.Commands[r"@\w+"] = _Command(func = self.at, description = "switch to speaker. @name, @all, @others, @any")
    authoritativeSystem.Commands[r"/A\d+(A\d+)?"] = _Command(func = self.SwitchUp, description = "switch up context")
    authoritativeSystem.Commands[r"/V\d+(V\d+)?"] = _Command(func = self.SwitchDown, description = "switch down context")
    authoritativeSystem.Commands[r"/new"] = _Command(func = self.newContext, description = "start a new context")
    authoritativeSystem.Commands[r"/sysMsg"] = _Command(func = self.sysMessage, description = "send message as the system")
    authoritativeSystem.Commands[r"/invite"] = _Command(func = self.invite, description = "invite a proxy to a collective")

  
  def invite(self, prompt, command, proxy):
    prompt = prompt.replace(command, "")
    prompt = prompt.strip()    
    proxy.invite(prompt)
    
    globalLogger.log(logLevel=LogLevel.authoritativeLog, message=f"{prompt} invited to the collective")
    
    return ""
  
  def sysMessage(self, prompt, command, proxy):
    prompt = prompt.replace(command, "")
    prompt = prompt.strip()
    proxy.context.senderRole = "system"
    proxy.ReceiveMessage(message = prompt, role = "system", roleName = "system")
    globalLogger.log(logLevel=LogLevel.authoritativeLog, message=f"message sent as 'system'")
    return ""
    
  def removeLast(self, prompt, command, proxy):
    globalLogger.log(logLevel=LogLevel.authoritativeLog, message=f"removing last message: {prompt}")
    if(prompt.startswith("<<<<")):
      proxy.context.RemoveLast() 
      proxy.context.RemoveLast() 
      globalLogger.log(logLevel=LogLevel.authoritativeLog, message="last 2 messages removed")
    elif (prompt.startswith("<<")):
      proxy.context.RemoveLast() 
      globalLogger.log(logLevel=LogLevel.authoritativeLog, message="last message removed")
    proxy.commitContext()     
    proxy.shouldGenerate = False
    return ""
  
  
  def regen(self, prompt, command, proxy):
    content = proxy.context.lastMessageObj.content
    role = proxy.context.lastMessageObj.role
    roleName = proxy.context.lastMessageObj.roleName
    proxy.context.RemoveLast()
    proxy.context.RemoveLast() 
    msg = proxy.context.lastMessageObj
    proxy.ReceiveMessage(message = content, role = role, roleName = roleName)
    return ""
    
    
  def at(self, prompt, command, proxy):
    atProxy = command
    prompt = prompt.replace(atProxy, "")
    prompt = prompt.strip()
    atProxy = atProxy.strip("@")    
    if(atProxy.lower() == "any"):
      proxy.SwitchToAny(prompt)
    elif(atProxy.lower() == "all"):
      proxy.All(prompt)
      return ""
    elif(atProxy.lower() == "others"):
      proxy.Others(prompt)
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
    globalLogger.log(logLevel=LogLevel.authoritativeLog, message="New conversation started")
    
    
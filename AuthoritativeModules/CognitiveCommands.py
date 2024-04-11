import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
from CognitiveSystem import cognitiveSystem
from Memory import globalMemory
import re
from _Command import _Command

class CognitiveCommands(object):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
  
  def RegisterCommands(self, authoritativeSystem):
    authoritativeSystem.Commands["/system2"] = _Command(func = self.system2, description = "switch to system2")
    authoritativeSystem.Commands[r"/remember"] = _Command(func = self.remember, description = "force commit to memory")
    authoritativeSystem.Commands[r"/reflect"] = _Command(func = self.reflect, description = "reflect upon the conversation and add to extended core")
    authoritativeSystem.Commands[r"/recall"] = _Command(func = self.recall, description = "recall a specific subject and add to extended context")
    authoritativeSystem.Commands[r"/resetRecall"] = _Command(func = self.resetRecall, description = "reset extended context")
    authoritativeSystem.Commands[r"/understand"] = _Command(func = self.understand, description = "force a fact to the factual memory")
    authoritativeSystem.Commands[r"/tag (\w|_)+"] = _Command(func = self.tag, description = "tag the conversation with a given subject")
    
  def system2(self, proxy, prompt, command):
    prompt = prompt.replace(command, "")
    cognitiveSystem.params["system"] = "system2"
    return prompt
  
  def remember(self, proxy, prompt, command):
    prompt = prompt.replace(command, "")
    cognitiveSystem.params["remember"] = True
    return prompt
  
  def reflect(self, proxy, prompt, command):
    prompt = prompt.replace(command, "")
    cognitiveSystem.params["reflect"] = True
    return prompt    
  
  def recall(self, proxy, prompt, command):
    prompt = prompt.replace(command, "")
    cognitiveSystem.params["recall"] = True
    return prompt
  
  def resetRecall(self, proxy, prompt, command):
    prompt = prompt.replace(command, "")
    cognitiveSystem.params["resetRecall"] = True
    return prompt
  
  def understand(self, proxy, prompt, command):
    prompt = prompt.replace(command, "")
    globalMemory.Understand(proxy, prompt)
    return ""

  
  def tag(self, proxy, prompt, command):
    prompt = prompt.replace(command, "")
    tag = command.replace("/tag ", "")
    globalMemory.TagMemory(proxy.context.ContextID, tag)
    return prompt
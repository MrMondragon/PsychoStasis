import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
from AuthoritativeSystem import authoritativeSystem
from CognitiveSystem import cognitiveSystem
from Memory import globalMemory
import re

class CognitiveCommands(object):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
  
  def RegisterCommands(self):
    authoritativeSystem.Commands["/system2"] = tuple(func = self.system2, descriptrion = "switch to system2")
    authoritativeSystem.Commands[r"/remember"] = tuple(func = self.remember, descriptrion = "force commit to memory")
    authoritativeSystem.Commands[r"/reflect"] = tuple(func = self.reflect, descriptrion = "reflect upon the conversation and add to extended core")
    authoritativeSystem.Commands[r"/recall"] = tuple(func = self.recall, descriptrion = "recall a specific subject and add to extended context")
    authoritativeSystem.Commands[r"/resetRecall"] = tuple(func = self.resetRecall, descriptrion = "reset extended context")
    authoritativeSystem.Commands[r"/tag (\w|_)+"] = tuple(func = self.tag, descriptrion = "tag the conversation with a given subject")
    
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
  
  def tag(self, proxy, prompt, command):
    prompt = prompt.replace(command, "")
    tag = command.replace("/tag ", "")
    globalMemory.TagMemory(proxy, tag)
    return prompt
import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
from CognitiveSystem import cognitiveSystem
from LongTermMemory import longTermMemory
from ShortTermMemory import shortTermMemory
from MemoryTypes import MemoryLevel
import re
from _Command import _Command

class CognitiveCommands(object):
  def __init__(self, **kwargs):
    pass
  
  def RegisterCommands(self, authoritativeSystem):
    authoritativeSystem.Commands[r"/memorize"] = _Command(func = self.memorize, description = "force commit to memory")
    authoritativeSystem.Commands[r"/remember"] = _Command(func = self.remember, description = "remember a specific subject and add to short term memory")
    authoritativeSystem.Commands[r"/rememberSummary"] = _Command(func = self.rememberSummary, description = "remember (summary level) a specific subject and add short term memory")
    authoritativeSystem.Commands[r"/rememberTextual"] = _Command(func = self.rememberTextual, description = "remember (textual level) a specific subject and add short term memory")
    authoritativeSystem.Commands[r"/resetMemory"] = _Command(func = self.resetMemory, description = "reset extended context")
    authoritativeSystem.Commands[r"/understand"] = _Command(func = self.understand, description = "force a fact to the Abstract memory")
  
  def memorize(self, proxy, prompt, command):
    cognitiveSystem.RunProcess(proxy = proxy, procName = "CommitToEpisodicMemory")
    cognitiveSystem.RunProcess(proxy = proxy, procName = "CommitToSummaryMemory")
    return ""
  
  def remember(self, proxy, prompt, command):
    prompt = prompt.replace(command, "")
    shortTermMemory.ElicitMemory(text = prompt, proxy = proxy, memoryLevel = MemoryLevel.Abstract)
    return ""
  
  def rememberSummary(self, proxy, prompt, command):
    prompt = prompt.replace(command, "")
    shortTermMemory.ElicitMemory(text = prompt, proxy = proxy, memoryLevel = MemoryLevel.Summary)
    return ""  

  def rememberTextual(self, proxy, prompt, command):
    prompt = prompt.replace(command, "")
    shortTermMemory.ElicitMemory(text = prompt, proxy = proxy, memoryLevel = MemoryLevel.Textual)
    return ""  

  
  def resetMemory(self, proxy, prompt, command):
    shortTermMemory.attentionContext = {}
    return ""
  
  def understand(self, proxy, prompt, command):
    cognitiveSystem.RunProcess(proxy = proxy, procName = "CommitToAbstractMemory")
    return ""
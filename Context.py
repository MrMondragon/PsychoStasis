import uuid
import copy
import math
import json
import datetime
from Nexus import globalNexus
from ShortTermMemory import shortTermMemory
from ContextEntry import ContextEntry
from typing import List
from Logger import globalLogger, LogLevel
  
class Context(object):
  def __init__(self, proxy) -> None:
    self.parentContext = None
    self.contextID = uuid.uuid4()
    self.messageHistory : List[ContextEntry] = []
    self.extendedSystem : List[ContextEntry] = []
    self.systemMessage = None
    self.windowSize = 3072 - 512 #typical context - typical max tokens
    self.lastMessageTxt = None    
    self.lastMessageObj = None
    self.lastAnswerTxt = None
    self.lastAnswerObj = None
    self.userName = "Ergo"
    self.verbose = False
    self.collective = None
    self.proxy = proxy
    self.messageSender = None
    self.senderRole = None
    self.model = None
    self.sessionStart = None
  
  
  def filteredHistory(self):
    return list(filter(lambda x: x.role != "ignore", self.messageHistory))
  
  def getContextWindow(self, msg):
    
    roleName = self.senderRole
    if(not roleName):
      roleName = self.userName
    
    if(msg):
      prompt = ContextEntry(role=roleName, content=msg, roleName = self.userName, context=self)
    
    totalTokens = prompt.tokensSize
    history = self.filteredHistory()
    
    window = []
    
    if(totalTokens > self.windowSize):
      tokenCount = 0
            
      if(self.systemMessage):
        tokenCount += self.systemMessage.tokensSize
      
      tokenCount += self.lastMessageObj.tokensSize
      
      if(len(history) > 0):
        tokenCount += history[0].tokensSize
        window.append(history[0])
        
        if(len(history) > 1):
          revWindow = []
          
          for message in reversed(history[1:]):
            tokenCount += message.tokensSize
            if(tokenCount <= self.windowSize):
              revWindow.append(message)
            else:
              break
                        
          window.extend(reversed(revWindow))
        
    else:
      window.extend(history)
    
    if(prompt):
      self.AppendMessage(msg, role=roleName, roleName = roleName)
      
    window.append(prompt)
    
    return window
    
  
  def getRelevantContext(self, prompt, contextCallback=None, start = None, end = None):
    relevantContext = []

    if(self.systemMessage):
      relevantContext.append(self.systemMessage)
      
    if(contextCallback):
      relevantContext.extend(contextCallback())
      
    if(hasattr(self, "extendedSystem")):
      if(self.extendedSystem):
        relevantContext.extend(self.extendedSystem)
      
    #Get attentionContext
    relevantContext.extend([memory.toContextEntry(self) for memory in  shortTermMemory.attentionContext.values()])
      
    historyWindow = self.getContextWindow(prompt)
    relevantContext.extend(historyWindow)
    
    if(self.verbose):
      globalLogger.log(logLevel=LogLevel.globalLog, message=f"Context: {json.dumps(relevantContext, indent=2)}")
      
    if(start and end):
      relevantContext = relevantContext[start:end]
    elif(start):
      relevantContext = relevantContext[start:]
    elif(end):
      relevantContext = relevantContext[:end]
      
    return relevantContext    
  
  
  def getRelevantContextAsText(self, prompt, start = None, end = None):
    context = self.getRelevantContext(prompt=prompt, start=start, end=end)
    result = ""
    for message in context:
      result += message.role + ": " + message.content+"\n"
    return result
  
  
  def SetSystemMessage(self, message):
    self.systemMessage = ContextEntry(role="system", content=message, roleName="system", context=self)
  
        
  def AppendMessage(self, message, role, roleName):
    if(message):
      messageObj = ContextEntry(role=role, content=message, roleName=roleName, context=self)
      self.lastMessageTxt = message
      self.lastMessageObj = messageObj
      self.linkMessage(messageObj)
      self.messageHistory.append(messageObj)
      if(self.verbose):
        globalLogger.log(logLevel=LogLevel.globalLog, message=f"Message: {self.lastMessageTxt}")
      return messageObj
    else:
      return None
  
  
  def AppendAnswer(self, role, answer):
    msgObject = self.model.FormatAnswer(answer = answer, role = role, context = self)
    self.linkMessage(msgObject)
    self.messageHistory.append(msgObject)
    self.lastAnswerObj = msgObject
    self.lastAnswerTxt = msgObject.content
    if(self.verbose):
      globalLogger.log(logLevel=LogLevel.globalLog, message=f"Answer: {self.lastAnswerTxt}")
    return msgObject
  

  def linkMessage(self,message):
    if(len(self.messageHistory) > 0):
      self.messageHistory[-1].next = message
      message.previous = self.messageHistory[-1]

  def GetUncommitedMessages(self, processName, frequency):
    history = self.filteredHistory()
    
    if(frequency == -1):
      return history
    
    history = list(filter(lambda x: processName not in x.commitedProcesses, history))

    if(len(history)> frequency):
      for message in history:
        message.CommitProcess(processName)
      globalLogger.log(logLevel=LogLevel.globalLog, message=f"{processName} uncommited: len(history) -- frequency: {frequency}")
      
      return history
    else:
      return []
    
    
  def TabulaRasa(self):
    for message in self.messageHistory:
      message.commitedProcesses = []

  def calcTokenCount(self, message):
    message.tokensSize, message.tokens = globalNexus.CalcTokenSize(message.content)
    
  def RemoveLast(self):
    lastMsg = self.messageHistory.pop()
    if(lastMsg.role != "user"):
      self.lastAnswerObj = None
    else:
      self.lastMessageObj = None
    globalLogger.log(logLevel=LogLevel.authoritativeLog, message=f"Message removed: {lastMsg.content}")

  
  def SwitchUp(self, n, l):
    msgs = self.messageHistory[-n:]
    self.messageHistory = self.messageHistory[0:-n]
    upperPart = self.messageHistory[0:-l]
    lowerPart = self.messageHistory[-l:]
    
    self.messageHistory = upperPart + msgs + lowerPart
  
  
  def SwitchDown(self, n,l):
    k = n+l
    msgs = self.messageHistory[-k:-l]
    
    upperPart = self.messageHistory[0:-k]
    lowerPart = self.messageHistory[-l:]
    
    self.messageHistory = upperPart + lowerPart + msgs
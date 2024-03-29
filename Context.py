import uuid
import copy
import math
import json
import datetime
from Nexus import globalNexus
from Memory import globalMemory
  
class Context(object):
  def __init__(self) -> None:
    self.parentContext = None
    self.contextID = uuid.uuid4()
    self.message_history = []
    self.systemMessage = None
    self.window_size = 3072 - 512 #typical context - typical max tokens
    self.proxyInteractionCounter = {}
    self.last_message = None    
    self.last_answer = None
    self.userName = "Ergo"
    self.verbose = False
    self.collective = None
    self.proxy = None
    self.messageSender = None
    self.senderRole = None
    self.model = None
    self.sessionStart = None
  
  def getContextWindow(self, prompt):
    totalTokens = self.get_token_count(prompt=prompt)
    if(totalTokens > self.window_size):
      window = []
      tokenCount = 0
      
      tokenCount += globalMemory.GetRecollectionContextSize(maxSize=self.window_size//2)
      
      if(self.systemMessage):
        tokenCount += self.get_token_size(self.systemMessage)
        
      tokenCount += self.get_token_size(prompt)
      
      if(len(self.message_history) > 0):
        if(self.sessionStart == None):
          tokenCount += self.message_history[0]["tokens"]
          window.append(self.message_history[0])
        else:
          tokenCount += self.sessionStart["tokens"]  
          window.append(self.sessionStart)
        
        if(len(self.message_history) > 1):
          revWindow = []
          
          for message in reversed(self.message_history[1:]):
            tokenCount += message["tokens"]
            if(tokenCount <= self.window_size):
              revWindow.append(message)
            else:
              break
                        
          window.extend(reversed(revWindow))
        
      windowList = []
      for message in window:
        windowList.append(self.convert_to_chat_format(message, includeTokens=False))
    else:
      windowList = []
      for message in self.message_history:
        windowList.append(self.convert_to_chat_format(message, includeTokens=False))
    
    return windowList
    
  def get_token_size(self, message):
    if(self.model != None):
      return len(self.model.encode(message))
    else:
      return len(globalNexus.CortexModel.encode(message))
  
  def get_token_count(self, prompt):
    tokenCount = 0
    if(len(self.message_history) > 0):
      for message in self.message_history:
        tokenCount += int(message["tokens"])      

    if(self.systemMessage):
      tokenCount += self.get_token_size(self.systemMessage)
      
    tokenCount += self.get_token_size(prompt)
    return tokenCount
    
  def convert_to_chat_format(self, message, includeTokens=True):
    if(includeTokens):
      return {"role":message["role"], "content":message["content"], "tokens":message["tokens"]}
    else:
      return {"role":message["role"], "content":message["content"]}
  
  def get_relevant_context(self, prompt, contextCallback=None, start = None, end = None):
    relevantContext = []
    if(self.systemMessage):
      relevantContext.append({"role":"system", "content":self.systemMessage})

    if(globalMemory.GetRecollectionContextSize() > 0):
      recollection = globalMemory.GetRecollectionContext(maxSize=self.window_size/2)
      relevantContext.extend(map(lambda x: {"role":"system", "content":x}, recollection))
    
    if(contextCallback):
      relevantContext.extend(contextCallback())

    if(prompt):
      promptMessage = self.append_message(prompt, role="user", roleName = self.userName)
      if(not self.sessionStart):
        self.sessionStart = self.convert_to_chat_format(promptMessage, includeTokens=True)
      
    historyWindow = self.getContextWindow(prompt=prompt)
    relevantContext.extend(historyWindow)
    
    if(self.verbose):
      print(f"Context: {json.dumps(relevantContext, indent=2)}")
      
    if(start and end):
      relevantContext = relevantContext[start:end]
    elif(start):
      relevantContext = relevantContext[start:]
    elif(end):
      relevantContext = relevantContext[:end]
      
    return relevantContext    
  
  def get_relevant_context_as_text(self, prompt, start = None, end = None):
    context = self.get_relevant_context(prompt=prompt, start=start, end=end)
    result = ""
    for message in context:
      result += message["role"] + ": " + message["content"]+"\n"
    
    return result
  
  def append_message(self, message, role, roleName):
    if(message):
      self.last_message = message
      messageId = f"{role}-{uuid.uuid4()}"
      tokens = self.get_token_size(message)    
      message = {"role":role, "content":message, "id":messageId,
                  "created":str(datetime.datetime.now()), "tokens":tokens, "roleName":roleName}
      self.message_history.append(message)
      if(self.verbose):
        print(f"Message: {self.last_message}")
    return message
  
  
  def append_answer(self, role, message):
    id = message["id"]
    id = id.replace("chatcmpl", role)
    msg = message["choices"][0]["message"]["content"]
    if(msg):
      while r"\n" in msg:
        msg = msg.replace(r"\n", "\n")
        
      if(msg.startswith(f"{role}: ")):
        msg=msg.replace(f"{role}: ", "")
        
      msgObject = {"role":"assistant", "content":msg, "id":id, "created":str(datetime.datetime.now()),
                  "tokens":message["usage"]["completion_tokens"], "roleName":role}
      self.message_history.append(msgObject)
      self.last_answer = msg
      
      if not role in self.proxyInteractionCounter:
        self.proxyInteractionCounter[role] = 0
        
      self.proxyInteractionCounter[role] += 1
      
      if(self.verbose):
        print(f"Answer: {self.last_answer}")

    
  def remove_last(self):
    lastMsg = self.message_history.pop()
    if(lastMsg["role"] != "user"):
      self.last_answer = None
    else:
      self.last_message = None
    print("Last message removed")
      
  
    
  def getChunks(self, chunkSize, chunkIndex):
    chunks = []
    start = chunkSize * chunkIndex
    end = start+chunkSize
    
    if(start > len(self.message_history)):
      return chunks
    
    if(end > len(self.message_history)):
      end = len(self.message_history)    
    
    for i in range(start, end):
      chunks.append(self.message_history[i])
    return chunks
  
  def GetChunkCount(self, chunkSize):
    return math.ceil(len(self.message_history) / chunkSize)
    

  def switchUp(self, n, l):

    msgs = self.message_history[-n:]
    self.message_history = self.message_history[0:-n]
    upperPart = self.message_history[0:-l]
    lowerPart = self.message_history[-l:]
    
    self.message_history = upperPart + msgs + lowerPart
  
  
  def switchDown(self, n,l):
    k = n+l
    msgs = self.message_history[-k:-l]
    
    upperPart = self.message_history[0:-k]
    lowerPart = self.message_history[-l:]
    
    self.message_history = upperPart + lowerPart + msgs
    



  
  
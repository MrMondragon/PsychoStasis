import uuid
import copy
import math
import json
import datetime
from Nexus import globalNexus
  
class Context(object):
  def __init__(self) -> None:
    self.parentContext = None
    self.contextID = uuid.uuid4()
    self.message_history = []
    self.systemMessage = None
    self.window_size = 2048 - 512 #typical context - typical max tokens
    self.last_message = None
    self.contextual_info = None
    self.last_answer = None
    self.userName = "Liam"
    self.verbose = False
    self.collective = None
    self.proxy = None
    self.messageSender = None
    self.senderRole = None
    self.model = None
  
  def getContextWindow(self, prompt):
    totalTokens = self.get_token_count(prompt=prompt)
    if(totalTokens > self.window_size):
      window = []
      tokenCount = 0
      if(self.contextual_info):
        tokenCount += self.get_token_size(self.contextual_info)
      if(self.systemMessage):
        tokenCount += self.get_token_size(self.systemMessage)
        
      tokenCount += self.get_token_size(prompt)
      
      if(len(self.message_history) > 0):
        tokenCount += self.message_history[0]["tokens"]
        window.append(self.message_history[0])
        
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
      
    if(self.contextual_info):
      tokenCount += self.get_token_size(self.contextual_info)
      
    tokenCount += self.get_token_size(prompt)
    return tokenCount
    
  def convert_to_chat_format(self, message, includeTokens=True):
    if(includeTokens):
      return {"role":message["role"], "content":message["content"], "tokens":message["tokens"]}
    else:
      return {"role":message["role"], "content":message["content"]}
  
  def get_relevant_context(self, prompt, contextCallback=None):
    relevantContext = []
    if(self.systemMessage):
      relevantContext.append({"role":"system", "content":self.systemMessage})
    historyWindow = self.getContextWindow(prompt=prompt)
    relevantContext.extend(historyWindow)
    
    if(contextCallback):
      relevantContext.extend(contextCallback())
    
    if(self.contextual_info):
      relevantContext.append({"role":"system", "content":self.contextual_info})
    if(prompt):
      promptMessage = self.append_message(prompt, role="user")
      relevantContext.append(self.convert_to_chat_format(promptMessage, includeTokens=False))
    if(self.verbose):
      print(f"Context: {json.dumps(relevantContext, indent=2)}")
    return relevantContext    
  
  def get_relevant_context_as_text(self, prompt):
    context = self.get_relevant_context(prompt=prompt)
    result = ""
    for message in context:
      result += message["role"] + ": " + message["content"]+"\n"
    
    return result
  
  def append_message(self, message, role):
    self.last_message = message
    messageId = f"{role}-{uuid.uuid4()}"
    tokens = self.get_token_size(message)    
    message = {"role":role, "content":message, "id":messageId,
                 "created":str(datetime.datetime.now()), "tokens":tokens}
    self.message_history.append(message)
    if(self.verbose):
      print(f"Message: {self.last_message}")
    return message
  
  
  def append_message_object(self, role, message):
    id = message["id"]
    id = id.replace("chatcmpl", role)
    msg = message["choices"][0]["message"]["content"]
    msgObject = {"role":role, "content":msg, "id":id, "created":str(datetime.datetime.now()),
                 "tokens":message["usage"]["completion_tokens"]}
    self.message_history.append(msgObject)
    self.last_answer = msg
    if(self.verbose):
      print(f"Answer: {self.last_answer}")

    
  def remove_last(self):
    lastMsg = self.message_history.pop()
    if(lastMsg["role"] != "user"):
      self.last_answer = None
    else:
      self.last_message = None
      
  def remove_last_pair(self):
    self.message_history.pop()
    self.message_history.pop()
    self.last_answer = None
    self.last_message = None
    
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
    




  
  
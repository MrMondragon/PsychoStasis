import datetime
import uuid


class ContextEntry(object):
  def __init__(self, role, content, roleName, context, id=""):
    self.role = role
    self.content = content
    self.tokens = None
    self.tokensSize = 0
    
    if(role != "ignore"):
      context.calcTokenCount(self)
      
    self.roleName = roleName
    self.created = str(datetime.datetime.now())
    
    if(not id):
      id =f"{role}-{uuid.uuid4()}"
    
    self.id = id
    self.previous = None
    self.next = None
    self.commitedProcesses = []
    
  
  def CommitProcess(self, processName):
    self.commitedProcesses.append(processName)
  
  def GetDictionary(self):
    return {
      "role": self.role,
      "content": self.content,
      "id": self.id,
    }
    
  def __str__(self) -> str:
    return str(self.GetDictionary())
    
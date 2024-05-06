from enum import Enum
import math
from ContextEntry import ContextEntry


class RecollectionLevel(Enum):
  Thematic = 0
  Abstract = 1
  DeepAbstract = 2
  Summary = 3
  DeepSummary = 4
  Episodic = 5
  
class MemoryLevel(Enum):
  Thematic = 0
  Abstract = 1 #old factual memory
  Entity = 2  
  Summary = 3
  Episodic = 4
  Documental = 5
  
class MemoryEntry:
  def __init__(self, context, content, timestamp, metadata, contextid, id, parent, distance = math.inf):
    self.content = content
    self.priority = math.inf
    self.timestamp = timestamp
    self.metadata = metadata
    self.tokensSize = 0
    self.tokens = None    
    self.parent = parent
    context.calcTokenCount(self)
    self.contextid = contextid
    self.distance = distance
    self.id = id
    
  
  def toContentEntry(self, context):
    role = self.metadata["proxy"]
    return ContextEntry(role = role, content = self.content, reoleName = role,
                        context=context, id=self.id)
    
  @classmethod
  def FromMemory(cls, id, content, metadata, distance, context):
    return MemoryEntry(context = context, content = content, timestamp=metadata["timestamp"], metadata = metadata, contextid=metadata["conversationId"], id=id, distance=distance, parent= metadata["parent"])  
  
  def __str__(self):
    return str({"content":self.content, "priority":self.priority, "timestamp":self.timestamp, "metadata":self.metadata, "tokensSize":self.tokensSize, "tokens":self.tokens, "contextid":self.contextid, "parent":self.parent, "distance":self.distance, "id":self.id})
  

    
    
  
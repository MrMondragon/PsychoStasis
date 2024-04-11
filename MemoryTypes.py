from enum import Enum


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
  Summary = 2
  Episodic = 3
  Entity = 4
  Documental = 5
  
class MemoryEntry:
  def __init__(self, content, priority, timestamp, metadata, tokenSize, contextID):
    self.content = content
    self.priority = priority
    self.timestamp = timestamp
    self.metadata = metadata
    self.tokenSize = tokenSize
    self.contextID = contextID
    
  
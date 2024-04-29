import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
sys.path.insert(0, str(Path(".")))
import uuid
from LongTermMemory import longTermMemory
from MemoryTypes import MemoryLevel
from Nexus import globalNexus
from _BaseCognitiveProcess import BaseCognitiveProcess


class CommitToEpisodicMemory(BaseCognitiveProcess):
  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.shouldRun = True
    self.Name = "CommitToEpisodicMemory"
    self.contexts = ["afterMessageReceived"] if "contexts" not in kwargs else kwargs["contexts"]
    self.frequency = 5 if "frequency" not in kwargs else kwargs["frequency"] #10
    self.shouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.common = True
    self.priority = 100
    
    
  def _internalRun(self):
    super()._internalRun()
    globalNexus.BeginShardBatch("Embeddings.Embeddings")
    conversationId=self.proxy.context.contextID
    documents = []
    ids = []
    metadata = []
    for message in self.localContext:
      if(message.role == "assistant"):
        role = self.proxy.name
      else:
        role = message.role
        
      previous = str(message.previous.id) if message.previous else ""
      nxt = str(message.next.id) if message.next else ""       
      
      
      data = longTermMemory.CreateEpisodicMetadata(conversationId=str(conversationId),
                                                role=role,
                                                proxy = self.proxy.name,
                                                next=nxt,
                                                previous=previous,
                                                id = message.id)
      documents.append(message.content)
      ids.append(message.id)
      metadata.append(data)
              
    longTermMemory.CommitToMemory(proxy=self.proxy, memoryLevel=MemoryLevel.Episodic, documents=documents, metadata=metadata, ids=ids)
    globalNexus.EndShardBatch("Embeddings.Embeddings")
    return documents
      
      
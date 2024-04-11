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
    self.frequency = 0 if "frequency" not in kwargs else kwargs["frequency"]
    self.shouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.common = True
    self.priority = 100
    
    
  def _internalRun(self, localContext):
    super()._internalRun()
    texContext = "\n".join([message.content for message in localContext])
    sentiment = globalNexus.getSentiment(texContext, nuanced=False)
    nuancedSentiment = globalNexus.getSentiment(texContext, nuanced=True)
    conversationId=self.proxy.context.contextID
    documents = []
    ids = []
    metadata = []
    for message in localContext:
      if(message.role == "assistant"):
        role = self.proxy.name
      else:
        role = message.role
        
      previous = str(message.previous.id) if message.previous else ""
      nxt = str(message.next.id) if message.next else ""       
      
      print(f"Next: {nxt}, Previous: {previous}")
      
      data = longTermMemory.CreateEpisodicMetadata(conversationId=str(conversationId),
                                                role=role,
                                                proxy = self.proxy.name,
                                                sentiment=sentiment,
                                                nuancedSentiment=nuancedSentiment,
                                                next=nxt,
                                                previous=previous)
      documents.append(message.content)
      ids.append(message.id)
      metadata.append(data)
              
    longTermMemory.CommitToMemory(proxy=self.proxy, memoryLevel=MemoryLevel.Episodic, documents=documents, metadata=metadata, ids=ids)
    return localContext
      
      
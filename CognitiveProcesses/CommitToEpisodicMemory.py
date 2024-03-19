import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
sys.path.insert(0, str(Path(".")))
import uuid
from Memory import globalMemory
from Nexus import globalNexus
from _BaseCognitiveProcess import BaseCognitiveProcess

class CommitToEpisodicMemory(BaseCognitiveProcess):
  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.shouldRun = True
    self.Name = "CommitToEpisodicMemory"
    self.contexts = ["afterMessageReceived"] if "contexts" not in kwargs else kwargs["contexts"]
    self.frequency = 10 if "frequency" not in kwargs else kwargs["frequency"]
    self.shouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.common = True
    self.priority = 100
    
  def _internalRun(self, localContext):
    super()._internalRun()
    texContext = "\n".join([message["content"] for message in localContext])
    entities = globalNexus.getNER(texContext)
    sentiment = globalNexus.getSentiment(texContext, nuanced=False)
    conversationId=self.proxy.context.contextID
    documents = []
    ids = []
    metadata = []
    for message in localContext:
      if(message["role"] == "assistant"):
        role = self.proxy.name
      else:
        role = message["role"]         
      data = globalMemory.CreateEpisodicMetadata(conversationId=conversationId,
                                                role=role,
                                                proxy = self.proxy.name,
                                                entities=entities,
                                                sentiment=sentiment, 
                                                tags=[])
      documents.append(message["content"])
      ids.append(message["id"])
      metadata.append(data)
              
    globalMemory.CommitToMemory(memoryLevel="episodicMemory", documents=documents, metadata=metadata, ids=ids)
      
      
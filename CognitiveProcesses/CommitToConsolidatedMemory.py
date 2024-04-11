import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
sys.path.insert(0, str(Path(".")))
import uuid
from Memory import globalMemory
from MemoryTypes import MemoryLevel
from Nexus import globalNexus
from _BaseCognitiveProcess import BaseCognitiveProcess

class CommitToConsolidatedMemory(BaseCognitiveProcess):
  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.Name = "CommitToConsolidatedMemory"
    self.contexts = ["afterMessageReceived"] if "contexts" not in kwargs else kwargs["contexts"]
    self.frequency = -1 if "frequency" not in kwargs else kwargs["frequency"]
    self.shouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.common = True
    self.priority = 110
    
    
  def _internalRun(self, localContext):
    super()._internalRun()
    texContext = "\n".join([message["content"] for message in localContext])
    conversationId=str(self.proxy.context.contextID)
    id=str(uuid.uuid4())
    
    summary = globalNexus.summarize(texContext)
    entities = globalNexus.getNER(summary)
    
    data = globalMemory.CreateSimpleMetadata(conversationId=conversationId,
                                            proxy=self.proxy.name)
    globalMemory.CommitToMemory(proxy=self.proxy, memoryLevel=MemoryLevel.Summary, documents=[summary], metadata=[data], ids=[id])
    globalMemory.EntityfyMemory(proxy=self.proxy, conversationID=id, entities=entities)
    
    return summary


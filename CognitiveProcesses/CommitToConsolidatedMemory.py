import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
sys.path.insert(0, str(Path(".")))
import uuid
from Memory import globalMemory
from Nexus import globalNexus
from _BaseCognitiveProcess import BaseCognitiveProcess

class CommitToConsolidatedMemory(BaseCognitiveProcess):
  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.shouldRun = True
    self.Name = "CommitToConsolidatedMemory"
    self.contexts = ["afterMessageReceived"] if "contexts" not in kwargs else kwargs["contexts"]
    self.frequency = 30 if "frequency" not in kwargs else kwargs["frequency"]
    self.shouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.common = True
    self.priority = 120
    
  def _internalRun(self, localContext):
    super()._internalRun()
    texContext = "\n".join([message["content"] for message in localContext])
    conversationId=self.proxy.context.contextID
    summary = globalNexus.summarize(texContext)
    data = globalMemory.CreateSimpleMetadata(input = summary,
                                            conversationId=conversationId,
                                            proxy=self.proxy.name,
                                            tags=[])
    globalMemory.CommitToMemory(memoryLevel="consolidatedMemory", documents=[summary], metadata=[data], ids=[conversationId])


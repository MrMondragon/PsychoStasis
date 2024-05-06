import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
sys.path.insert(0, str(Path(".")))
import uuid
from LongTermMemory import longTermMemory
from MemoryTypes import MemoryLevel
from Nexus import globalNexus
from _BaseCognitiveProcess import BaseCognitiveProcess

class CommitToSummaryMemory(BaseCognitiveProcess):
  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.Name = "CommitToSummaryMemory"
    self.contexts = ["afterMessageReceived"] if "contexts" not in kwargs else kwargs["contexts"]
    self.frequency = 20 if "frequency" not in kwargs else kwargs["frequency"] #50
    self.shouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.common = True
    self.priority = 110
    
    
  def _internalRun(self):
    super()._internalRun()
    globalNexus.BeginShardBatch("Embeddings.Embeddings")
    
    txtContent, ids = longTermMemory.GetUnparentedMemories(memoryLevel=MemoryLevel.Episodic, proxy=self.proxy)
    conversationId=str(self.proxy.context.contextID)
    id=f"sum-{uuid.uuid4()}"
    
    summary = globalNexus.Summarize(txtContent)
    
    data = longTermMemory.CreateSimpleMetadata(conversationId=conversationId, proxy=self.proxy.name, id=id)
    data["episodes"] = ids
    longTermMemory.CommitToMemory(proxy=self.proxy, memoryLevel=MemoryLevel.Summary, documents=[summary], metadata=[data], ids=[id])
    longTermMemory.AssignParentToMemories(proxy=self.proxy, memoryLevel=MemoryLevel.Episodic, clusterId=id)
    globalNexus.EndShardBatch("Embeddings.Embeddings")
    
    return summary


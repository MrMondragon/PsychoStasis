import sys
from pathlib import Path
import grammars
sys.path.insert(0, str(Path("..")))
sys.path.insert(0, str(Path(".")))
import uuid
from Memory import globalMemory
from Nexus import globalNexus
from _BaseCognitiveProcess import BaseCognitiveProcess

class CommitToFactualMemory(BaseCognitiveProcess):
  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.shouldRun = True
    self.Name = "CommitToFactualMemory"
    self.contexts = ["afterMessageReceived"] if "contexts" not in kwargs else kwargs["contexts"]
    self.frequency = 20 if "frequency" not in kwargs else kwargs["frequency"]
    self.shouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.common = True
    self.priority = 110 # so that it runs after commit to episodic
    
  def _internalRun(self, localContext):
    super()._internalRun()
    conversationId=self.proxy.context.contextID
    self.proxy.enterSubContext(copySystem=False, start=self.Frequency*-1)
    facts = self.proxy.GenerateAnswer(prompt="Cite three facts you can gather from this conversation. Do not introduce yourself. Answer with the files only!", grammar=grammars.list)
    
    facts = facts.splitlines()
    if(facts):
      if(len(facts) > 3):
        facts = facts[-3:]
      documents = []
      ids = []
      metadata = []      
      for fact in facts:
        data = globalMemory.CreateSimpleMetadata(conversationId=conversationId,
                                                proxy=self.proxy.name,
                                                tags=[])
        documents.append(fact)
        ids.append(uuid.uuid4())
        metadata.append(data)
      globalMemory.CommitToMemory(memoryLevel="factualMemory", documents=documents, metadata=metadata, ids=ids)

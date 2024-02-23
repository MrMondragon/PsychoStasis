from Memory import globalMemory
from Nexus import globalNexus
from BaseCognitiveProcess import BaseCognitiveProcess
from Proxy import Proxy


class CommitToMemory(BaseCognitiveProcess):
  def __init__(self, name, **kwargs) -> None:
    super().__init__(name, **kwargs)
    self.shouldRun = True
    
  def _internalRun(self):
    super()._internalRun()
    self.commitToEpisodicMemory(innerThoughts=False)
    self.commitToEpisodicMemory(innerThoughts=True)
        
  def commitToEpisodicMemory(self, innerThoughts):
    localContext = self.getLocalContext(innerThoughts=innerThoughts)
    if(localContext != []):
      entities = globalNexus.getNER(str.join(iterable=localContext, sep="\n"))
      documents = []
      ids = []
      metadata = []
      for message in localContext:
        if(message["role"] == "assistant"):
          role = self.proxy.name
        else:
          role = message["role"]         
        document, data = globalMemory.CreateEpisodicMemory(input = message["content"],
                                                           conversationId=self.proxy.context.contextID,
                                                           role=role,
                                                           proxy = self.proxy.name,
                                                           entities=entities,
                                                           sentiment="", 
                                                           tags=[])
        documents.append(document)
        ids.append(message["id"])
        metadata.append(data)
      globalMemory.CommitToMemory(memoryLevel="episodicMemory", documents=documents, metadata=metadata, ids=ids)



    
    
      
    # add to episodic memory
    # update consolidated memory
    # try to extract facts
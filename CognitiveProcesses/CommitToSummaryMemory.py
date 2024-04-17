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
    self.frequency = 0 if "frequency" not in kwargs else kwargs["frequency"] #50
    self.shouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.common = True
    self.priority = 110
    
    
  def _internalRun(self, localContext):
    super()._internalRun()
    globalNexus.BeginShardBatch("Embeddings.Embeddings")
    globalNexus.BeginShardBatch("Summarizer.Summarizer")
    
    txtContent, ids = longTermMemory.GetUnparentedMemories(memoryLevel=MemoryLevel.Episodic, proxy=self.proxy)
    print(txtContent)
    conversationId=str(self.proxy.context.contextID)
    id=f"sum-{uuid.uuid4()}"
    
    summary = globalNexus.Summarize(txtContent)
    
    #query thr 1.2 to se if there's already a summary that represents this text.If so, update the metadata episodes
    summaryMemory = longTermMemory.AccessMemoryLevel(memoryLevel=MemoryLevel.Summary, proxy=self.proxy)
    queryResult = summaryMemory.query(query_texts=summary, n_results=1,  where={"conversationId": conversationId})
    #if no facts were found, set the distance to -1
    if(not len(queryResult["ids"][0])):
      distance = -1
    else:
      #otherwise, set the distance to the first result
      distance = queryResult["distances"][0][0]
      
    if((distance >= 1.2) or (distance == -1)):
      data = longTermMemory.CreateSimpleMetadata(conversationId=conversationId,
                                              proxy=self.proxy.name, id="")
      data["episodes"] = ids
    else:
      id = queryResult["ids"][0][0]
      txtContent = txtContent +"\n" + queryResult["documents"][0][0] 
      summary = globalNexus.Summarize(txtContent)

      data = queryResult["metadatas"][0][0]
      
      sIds = str(data["episodes"]).split("|")
      xIds = ids.split("|")
      sIds.extend(xIds)
      sIds = list(set(sIds))
      episodes = "|".join(sIds) 
      data["episodes"] = episodes
    
    data["id"] = id        
    
    longTermMemory.CommitToMemory(proxy=self.proxy, memoryLevel=MemoryLevel.Summary, documents=[summary], metadata=[data], ids=[id])
    longTermMemory.AssignParentToMemories(proxy=self.proxy, memoryLevel=MemoryLevel.Episodic, clusterId=id)
    globalNexus.EndShardBatch("Embeddings.Embeddings")
    globalNexus.EndShardBatch("Summarizer.Summarizer")
    
    return summary


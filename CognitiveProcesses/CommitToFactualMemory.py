import sys
from pathlib import Path
import grammars
sys.path.insert(0, str(Path("..")))
sys.path.insert(0, str(Path(".")))
import uuid
from LongTermMemory import longTermMemory
from Nexus import globalNexus
from _BaseCognitiveProcess import BaseCognitiveProcess

class CommitToAbstractMemory(BaseCognitiveProcess):
  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.shouldRun = True
    self.Name = "CommitToAbstractMemory"
    self.contexts = ["afterMessageReceived"] if "contexts" not in kwargs else kwargs["contexts"]
    self.frequency = -1 if "frequency" not in kwargs else kwargs["frequency"]
    self.shouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.common = True
    self.priority = 120 # so that it runs after episodic and consolidated
    self.factCount = 5
    
  def _internalRun(self, localContext):
    super()._internalRun()
    conversationId=str(self.proxy.context.contextID)
    
    #get all summaries that don't have parents
    summaries, summaryIds = longTermMemory.GetUnparentedMemories(memoryLevel="AbstractMemory")

    #generate N facts about the collection of summaries
    self.proxy.enterSubContext(copySystem=True)
    self.proxy.context.AppendMessage(role = "user", roleName=self.proxy.context.userName, message=summaries)
    facts = self.proxy.GenerateAnswer(prompt=f"Cite {self.factCount} facts you can gather from this conversation. Do not introduce yourself. Answer with the facts only!", grammar=grammars.list)
    self.proxy.exitSubContext()
    
    #split and strip the facts
    facts = facts.splitlines().strip('- ')
    
    #if facts are found
    if(facts):
      entities = globalNexus.getNER(facts)
      globalNexus.BeginShardBatch("Embeddings.Embeddings")
            
      facts = facts.splitlines()
      #remove the begining in case the model has introduced the facts
      if(len(facts) > self.factCount):
        facts = facts[-self.factCount:]
      documents = []
      ids = []
      metadata = []      
      for fact in facts:
        #get the closest fact to the fact at hand
        queryResult = longTermMemory.AbstractMemory.query(query_texts=fact, n_results=1,
                                 where={"conversationId": conversationId})
        
        #if no facts were found, set the distance to -1
        if(not len(queryResult["ids"])):
          distance = -1
        else:
          #otherwise, set the distance to the first result
          distance = queryResult["distances"][0][0]
        
        #if no distance was found or the distance is higher than the threshold, add the fact to the memory
        if((distance >= 1.2) or (distance == -1)):
          data = longTermMemory.CreateSimpleMetadata(conversationId=conversationId,
                                                  proxy=self.proxy.name)
          data["summaryIds"] = summaryIds
          documents.append(fact)
          factId = str(uuid.uuid4())
          ids.append(factId)
          metadata.append(data)
        else:
          id = queryResult["ids"][0][0]
          if id not in ids:
            ids.append(id)
            documents.append(queryResult["documents"][0][0])
            queryResult["metadatas"][0][0]["summaryIds"] = summaryIds
            metadata.append(queryResult["metadatas"][0][0])
      
      parentCluster = "|".join(ids)
      
      longTermMemory.CommitToMemory(memoryLevel="AbstractMemory", documents=documents, metadata=metadata, ids=ids)
      longTermMemory.EntityfyMemory(conversationID="|".join(ids), entities=entities)
      longTermMemory.AssignParentsToCluster(memoryLevel="AbstractMemory", clusterId=parentCluster)
      globalNexus.EndShardBatch("Embeddings.Embeddings") 
      
    return facts
      
      
    
    
    

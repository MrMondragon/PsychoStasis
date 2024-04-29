import sys
from pathlib import Path
import grammars
sys.path.insert(0, str(Path("..")))
sys.path.insert(0, str(Path(".")))
import uuid
from LongTermMemory import longTermMemory
from Nexus import globalNexus
from MemoryTypes import MemoryLevel
from _BaseCognitiveProcess import BaseCognitiveProcess
import re

class CommitToThematicMemory(BaseCognitiveProcess):
  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.shouldRun = True
    self.Name = "CommitToThematicMemory"
    self.contexts = ["afterMessageReceived"] if "contexts" not in kwargs else kwargs["contexts"]
    self.frequency = 50 if "frequency" not in kwargs else kwargs["frequency"] #50
    self.shouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.common = True
    self.priority = 150 # so that it runs after episodic and consolidated AND abstract
    self.themeCount = 5
    self.Shard = "ObjectiveDecisory.GGUF"
    globalNexus.LoadModel(self.Shard)
    
    
  def _internalRun(self):
    super()._internalRun()
    conversationId=str(self.proxy.context.contextID)
    globalNexus.BeginShardBatch("Embeddings.Embeddings")
    
    #get all abstract memories that don't have parents
    facts, factIds = longTermMemory.GetUnparentedMemories(memoryLevel=MemoryLevel.Abstract, proxy=self.proxy)

    #discover N themes about the collection of facts
    self.proxy.enterSubContext(copySystem=False)
    self.proxy.context.AppendMessage(role = "user", roleName=self.proxy.context.userName, message=facts)
    themes = self.proxy.GenerateAnswer(shard = self.Shard, prompt=f"List the main {self.themeCount} themes of this conversation, using single words or small expressions. Do not introduce yourself. Answer with the themes only!", grammar=grammars.list)
    self.proxy.exitSubContext()
    
    themes = themes.content
    if('\n' in themes):
      themes = themes.splitlines()
    else:
      themes = themes.split(', ')
    
    themeCount = len(themes)
    
    for i in range(themeCount): 
      theme = themes[i]
      pattern = r'\d+\S\s'
      match = re.search(pattern, theme)
      if match:
        theme = theme[match.end():]
      theme = theme.strip('- ')
      themes[i] = theme
    
    #remove the begining in case the model has introduced the themes
    #if(len(themes) > self.themeCount):
      #themes = themes[-self.themeCount:]
    #Not sure about this part after seeing the generated content
    
    entities = globalNexus.GetNER(facts)
    entities = list(entities.keys())
    themes.extend(entities)
    

    documents = []
    ids = []
    metadata = []      
    for theme in themes:
      #get the closest theme to the theme at hand
      thematicMemory = longTermMemory.AccessMemoryLevel(memoryLevel=MemoryLevel.Thematic, proxy=self.proxy)
      queryResult = thematicMemory.query(query_texts=theme, n_results=1,
                                where={"conversationId": conversationId})
      
      #if no themes were found, set the distance to -1
      if(not len(queryResult["ids"][0])):
        distance = -1
      else:
        #otherwise, set the distance to the first result
        distance = queryResult["distances"][0][0]
      
      #if no distance was found or the distance is higher than the threshold, add the theme to the memory
      if((distance >= 1.2) or (distance == -1)):
        data = longTermMemory.CreateSimpleMetadata(conversationId=conversationId,
                                                proxy=self.proxy.name, id=theme)
        data["factIds"] = factIds
        documents.append(theme)
        ids.append(theme)
        metadata.append(data)
      else:
        id = queryResult["ids"][0][0]
        if(id not in ids):
          ids.append(id)
          documents.append(queryResult["documents"][0][0])
          
          fIds = factIds.split("|")
          xIds = str(queryResult["metadatas"][0][0]["factIds"]).split("|")
          fIds.extend(xIds)
          fIds = list(set(fIds)) 
          factIds = "|".join(fIds)
          
          queryResult["metadatas"][0][0]["factIds"] = factIds
          metadata.append(queryResult["metadatas"][0][0])
    
    parentCluster = "|".join(ids)
    
    longTermMemory.CommitToMemory(memoryLevel=MemoryLevel.Thematic, documents=documents, metadata=metadata, ids=ids, proxy=self.proxy)
    longTermMemory.AssignParentToMemories(memoryLevel=MemoryLevel.Abstract, clusterId=parentCluster, proxy=self.proxy)
    globalNexus.EndShardBatch("Embeddings.Embeddings") 
      
    return themes
      
      
    
    
    

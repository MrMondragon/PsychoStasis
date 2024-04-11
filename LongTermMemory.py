from chromadb import PersistentClient, Client
from Nexus import NexusEmbeddingFunction, globalNexus
import datetime, time
from collections import deque
from MemoryTypes import RecollectionLevel, MemoryLevel, MemoryEntry
from typing import List

positive = ["yes", "sure", "ok", "okay", "yeah", "yup", "yep", "yea", "yah", "yas", "ya", "yap"]
negative = ["no", "nope", "nah", "nay", "nope", "nah", "nay"]
invalidChars = ["#", "@", "!", "$", "%", "^", "&", "*", "(", ")", "-", "_", "=", "+", "{", "}", "[", "]", "|", "\\", ":", ";", "'", "\"", "<", ">", ",", ".", "?", "/"]

positiveStr = " ".join(positive)
negativeStr = " ".join(negative)

basePriority = 500

class LongTermMemory(object):
  def __init__(self):
    self.path = './Memory/'
    self.persistent = False
    self.client = PersistentClient(self.path) if(self.persistent) else Client()
    
    self.recollectionContext : List[MemoryEntry] = []
    self.recollectionQueries : List[str] = []
  
    ###############################################################
    ################### Discriminatory Memories ###################
    ############################################################### 
    if(self.persistent):
      globalNexus.BeginShardBatch("Embeddings.Embeddings")
      self.booleanDiscriminationMemory = self.client.get_or_create_collection("booleanDiscriminationMemory",
                                                                            embedding_function=NexusEmbeddingFunction())
      if(self.booleanDiscriminationMemory.count() == 0):
        self.booleanDiscriminationMemory.add(documents=[negativeStr, positiveStr], ids=["0", "1"])
        
      self.closestWordMemory = self.client.get_or_create_collection("closestWordMemory",
                                                                    embedding_function=NexusEmbeddingFunction())
      if(self.closestWordMemory.count() == 0):
        with open("./models/vocab.txt", "r",  encoding="utf-8") as f:
          words = f.read().splitlines()
        words = list(filter(lambda s: not any(s.startswith(c) for c in invalidChars) and len(s)>2, words))
        ids = [f"id_{i}" for i in range(0, len(words))]
        self.closestWordMemory.add(documents=words, ids=ids)
      globalNexus.EndShardBatch("Embeddings.Embeddings")

    
  ###############################################################
  ################### Specialized Metadata ######################
  ###############################################################     
  def CreateEpisodicMetadata(self, conversationId, role, proxy,  previous, next):
    timestamp = int(time.mktime(datetime.datetime.now().timetuple()))
    metadata={
          "conversationId": str(conversationId), 
          "role": role,
          "proxy": proxy,
          "timestamp": timestamp,
          "previous": previous,
          "next": next,
          "parent": ""            
        }
    return metadata
  
  def CreateSimpleMetadata(self, conversationId, proxy):
    timestamp = int(time.mktime(datetime.datetime.now().timetuple()))
    metadata={
        "conversationId": str(conversationId), 
        "proxy": proxy,
        "timestamp": timestamp,
        "parent": ""
      }
    
    return metadata

  ###############################################################
  ################### Memory Manipulation  ######################
  ###############################################################     
  def AccessMemoryLevel(self, proxy, memoryLevel):
    if(proxy):
      levelName = f"{proxy.name}_{memoryLevel}"
    else:
      levelName = f"system_{memoryLevel}"
      
    memoryLevel = self.client.get_or_create_collection(levelName,
                                          embedding_function=NexusEmbeddingFunction())
    return memoryLevel  


  def QueryAll(self, proxy, memoryLevel, where = {}, queryTexts = [""]):
    memory = self.AccessMemoryLevel(memoryLevel=memoryLevel, proxy=proxy)
    ct = memory.count()
    query =memory.query(query_texts=queryTexts, n_results=ct, where=where,include=['metadatas','documents', 'distances',])
    return query

  #I firmly refuse to use metadatas as a plural for metadata!!!!
  def CommitToMemory(self, proxy, memoryLevel, documents, metadata, ids):
    memory = self.AccessMemoryLevel(memoryLevel=memoryLevel, proxy=proxy)
    memory.upsert(documents=documents, metadatas=metadata, ids=ids)
    
        
  def UpdateMemoryUniformMetadata(self, proxy,memoryLevel, query, metadata, maxRecords):
    memory = self.AccessMemoryLevel(memoryLevel=memoryLevel, proxy=proxy)
    ids = memory.query(where=query, n_results=maxRecords, include=[])
    metadataList = [metadata] * len(ids)
    memory.update(ids=ids, metadatas=metadataList)

    
  def UpdateMemoryMetadata(self, proxy, memoryLevel, ids, metadata):
    memory = self.AccessMemoryLevel(memoryLevel=memoryLevel, proxy=proxy)
    memory.update(ids=ids, metadatas=metadata)

    
  def Count(self, memoryLevel, where):
    query = self.QueryAll(memoryLevel, where)
    ids = query["ids"][0]
    return len(ids)
  
  
  def QueryDocuments(self, proxy, memoryLevel, where):
    query = self.QueryAll(proxy, memoryLevel, where)
    documents = query["documents"][0]
    return documents
    
    
  def GetItemsByTreshold(self, proxy, memoryLevel, where, threshold):
    query = self.QueryAll(proxy, memoryLevel, where)
    ids = query["ids"][0]
    count = len(ids)
    list = []
    for i in range(count):
      if query["distances"][0][i] <= threshold:
        list.append({"id": ids[i], "distance": query["distances"][0][i]})
    return list
  

  def UpsertConversationCollection(self, proxy, memoryLevel, conversationID, themeOrEntity):
    memory = self.AccessMemoryLevel(memoryLevel=memoryLevel, proxy=proxy)
    
    conversationID = str(conversationID)
    
    if not "|" in conversationID:
      conversations = [conversationID]
    else:
      conversations = conversationID.split('|')
    
    entry = memory.get(themeOrEntity)
    print(entry)

    if(len(entry["ids"][0]) == 0):
      memory.add(documents=[themeOrEntity], ids=[themeOrEntity], metadatas=[{"conversations": conversationID}])
    else:
      entryConversations = entry["metadatas"][0]["conversations"].split('|')
      conversations.extend(entryConversations)
      conversations = list(set(conversations))
      conversations = "|".join(conversations)
      memory.update(
        ids=[themeOrEntity],
        documents=[themeOrEntity],
        metadatas={"conversations": conversations},
      )
      
      
  def GetUnparentedMemories(self, proxy, memoryLevel):
    query = self.QueryAll(proxy = proxy, memoryLevel=memoryLevel, where={"parent": ""}, queryTexts=[""])
    documents = "\n".join(query["documents"][0])
    ids = "|".join(query["ids"][0])
    return documents, ids
  
  
  def AssignParentToMemories(self, proxy, memoryLevel, clusterId):
    query = self.QueryAll(proxy = proxy, memoryLevel=memoryLevel, where={"parent": ""}, queryTexts=[""])
    memory = self.AccessMemoryLevel(memoryLevel=memoryLevel, proxy=proxy)

    for i in range(len(query["ids"][0])):
      metadata = query["metadatas"][0][i]
      metadata["parent"] = clusterId      
      memory.update(ids=query["ids"][0], metadatas=query["metadatas"][0])
    
  def TabulaRasa(self, proxy):
    levels = [x.name for x in MemoryLevel.__members__.values()]
    for level in levels:
      self.client.delete_collection(f"{proxy.name}_{level}")
      
  ###############################################################
  ############# Thematization and Entityfication ################
  ###############################################################     
  def ThematizeMemory(self, proxy, conversationID, theme):
    self.UpsertConversationCollection(proxy = proxy, memoryLevel=MemoryLevel.Thematic, conversationID=conversationID, themeOrEntity=theme)
        
  def EntityfyMemory(self,  proxy, conversationID, entities):
    entities = list(entities.keys())
    for entity in entities:      
      self.UpsertConversationCollection(proxy = proxy, memoryLevel=MemoryLevel.Entity, conversationID=conversationID, themeOrEntity=entity)

  ###############################################################
  ####################### Recollection ##########################
  ###############################################################     
  def GetRecollectionContext(self, maxSize=1024):
    if(self.recollectionContext):
      ctx = deque()
      self.recollectionContext.sort(key = lambda x : x["priority"])
      ctx.extend(self.recollectionContext)
      
      while (sum(x["tokenSize"] for x in ctx) < maxSize):
        ctxSize += ctx[0]["tokenSize"]
        ctx.pop()
      
      self.recollectionContext = list(ctx) 
      return list(map(lambda x: x.text, self.recollectionContext)) 
    else:
      return []
    
  def GetRecollectionContextSize(self, maxSize=1024):
    return len(self.GetRecollectionContext(maxSize=maxSize))
    
  def ResetRecollectionContext(self):
    self.recollectionContext.clear()
    self.recollectionQueries.clear()
    
  def AddToRecollectionContext(self, text, priority, query, metadata):
    if((query not in self.recollectionQueries) and (text not in map(lambda x: x["text"], self.recollectionContext))):
      self.recollectionQueries.append(text)
      tokenSize = globalNexus.GetTokenCount(text)    
      self.recollectionContext.append({"text":text, "priority":priority, "tokenSize": tokenSize, "metadata": metadata})
  
  def ReprioritizeRecollectionContext(self, query):
    pass
  
  def Recall(self, query, clear=False, RecollectionLevel = RecollectionLevel.Abstract):
    if(clear):
      self.ResetRecollectionContext()
      
###############################################################
################## Long Term Memory Object ####################
###############################################################
longTermMemory = LongTermMemory()    
from chromadb import PersistentClient, Client
from Nexus import NexusEmbeddingFunction, globalNexus
import datetime, time
from MemoryTypes import RecollectionLevel, MemoryLevel, MemoryEntry
from typing import List
from Logger import globalLogger

positive = ["yes", "sure", "ok", "okay", "yeah", "yup", "yep", "yea", "yah", "yas", "ya", "yap"]
negative = ["no", "nope", "nah", "nay", "nope", "nah", "nay"]
invalidChars = ["#", "@", "!", "$", "%", "^", "&", "*", "(", ")", "-", "_", "=", "+", "{", "}", "[", "]", "|", "\\", ":", ";", "'", "\"", "<", ">", ",", ".", "?", "/"]

positiveStr = " ".join(positive)
negativeStr = " ".join(negative)


class LongTermMemory(object):
  def __init__(self):
    self.path = './Memory/'
    self.persistent = False
    self.client = PersistentClient(self.path) if(self.persistent) else Client()
  
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
  def CreateEpisodicMetadata(self, conversationId, role, proxy,  previous, next, id):
    timestamp = int(time.mktime(datetime.datetime.now().timetuple()))
    metadata={
          "conversationId": str(conversationId), 
          "role": role,
          "proxy": proxy,
          "timestamp": timestamp,
          "previous": previous,
          "next": next,
          "parent": "",
          "id": id
        }
    return metadata
  
  def CreateSimpleMetadata(self, conversationId, proxy, id):
    timestamp = int(time.mktime(datetime.datetime.now().timetuple()))
    metadata={
        "conversationId": str(conversationId), 
        "proxy": proxy,
        "timestamp": timestamp,
        "parent": "",
        "id": id
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
    if ct == 0:
      return None
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
    
    
  def GetItemsByTreshold(self, proxy, memoryLevel,  threshold, queryText = "", where = {}) -> List[MemoryEntry]:
    query = self.QueryAll(proxy, memoryLevel, where, queryTexts=[queryText])
    if(query == None):
      return None
    ids = query["ids"][0]
    count = len(ids)
    list = []
    for i in range(count):
      if (query["distances"][0][i] <= threshold) or (threshold == 0):
        entry = MemoryEntry.FromMemory(context = proxy.context, id = ids[i], content = query["documents"][0][i], metadata = query["metadatas"][0][i], distance=query["distances"][0][i])
        list.append(entry)
    return list
  

  def UpsertConversationCollection(self, proxy, memoryLevel, conversationID, themeOrEntity):
    memory = self.AccessMemoryLevel(memoryLevel=memoryLevel, proxy=proxy)
    
    conversationID = str(conversationID)
    
    if not "|" in conversationID:
      conversations = [conversationID]
    else:
      conversations = conversationID.split('|')
    
    entry = memory.get(themeOrEntity)
    globalLogger.log(entry)

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
      

#############################################################
################## Long Term Memory Object ####################
###############################################################
longTermMemory = LongTermMemory()    
from chromadb import PersistentClient, Client
from Nexus import NexusEmbeddingFunction, globalNexus
import datetime
from collections import deque

positive = ["yes", "sure", "ok", "okay", "yeah", "yup", "yep", "yea", "yah", "yas", "ya", "yap"]
negative = ["no", "nope", "nah", "nay", "nope", "nah", "nay"]
invalidChars = ["#", "@", "!", "$", "%", "^", "&", "*", "(", ")", "-", "_", "=", "+", "{", "}", "[", "]", "|", "\\", ":", ";", "'", "\"", "<", ">", ",", ".", "?", "/"]

positiveStr = " ".join(positive)
negativeStr = " ".join(negative)

basePriority = 500

class Memory(object):
  def __init__(self):
    self.path = './Memory/'
    self.client = PersistentClient(self.path)
    self.transientClient = Client()
  
    
    
    #  Context memory is not a collection!!
    #  it is a message list with priority which is manipulated by
    #  the cognitive system
    #  then the context of the proxy absorbs it partially or fully in priority order
    #  distance based information is inserted with the formula
    #  ((1/distance) * base priority) + base priority
    
    self.recollectionContext = [] # tuple(text, priority: float, metadata: dict, tokenSize: int, contextID: str)    
    self.recollectionQueries = []
    
    ### Context consumes memory and not the other way around (to avoid circular references)
    ### Check response with personality
    ###   does this answer align with your personality?
    ##      tell me a fact about you that shows this misalignment
    ##      feed fact back into extended core
    ##      rephrase it so that it better aligns with your personality
    
    #  evaluate each metadata to see if, when and how it will be used
    #  eg.: datetime can be used in a formula like this: ((today - datetime)/10) * basepriority) + basepriority
    #  other factors such as user sentiment, salience (not yet implemented) can also influence priority
    #   all this will be performed by the recall processes
    ###
    #  proxy core and extended core enter the list with priority 100 (basepriority / 5)
    #  this information comes from the not yet implemented reflectiveMemory
    
    #############  See if some of the commitToMemory code should be moved here
    

    ###############################################################
    ####################### General Memory ########################
    ###############################################################

    self.episodicMemory = self.client.get_or_create_collection("episodicMemory",
                                                               embedding_function=NexusEmbeddingFunction())
    
    self.factualMemory = self.client.get_or_create_collection("factualMemory",
                                                               embedding_function=NexusEmbeddingFunction())
    
    self.relationalMemory = self.client.get_or_create_collection("relationalMemory",
                                                             embedding_function=NexusEmbeddingFunction())
    
    self.consolidatedMemory = self.client.get_or_create_collection("consolidatedMemory",
                                                                   embedding_function=NexusEmbeddingFunction())
    #stores tags for vectorial search
    #tagging conversations as an authoritative command
    #tags are stored in the metadata as well as here
    #structure is {tag: [conversationId1, conversationId2, conversationId3]}
    self.tagMemory = self.client.get_or_create_collection("tagMemory",
                                                                   embedding_function=NexusEmbeddingFunction())

    ############################Study Private gpt to see the structure of documental memory
    
    ###############################################################
    ##################### Documental Memory #######################
    ###############################################################
    #raw text
    self.documentalMemoryLevel0 = self.client.get_or_create_collection("documentalMemoryLevel0",
                                                                       embedding_function=NexusEmbeddingFunction())
    #summarization level 1
    self.documentalMemoryLevel1 = self.client.get_or_create_collection("documentalMemoryLevel1",
                                                                       embedding_function=NexusEmbeddingFunction())
    #summarization level 2
    self.documentalMemoryLevel2 = self.client.get_or_create_collection("documentalMemoryLevel2",
                                                                       embedding_function=NexusEmbeddingFunction())
    
    ###############################################################
    ################### Discriminatory Memories ###################
    ###############################################################    
    
    self.booleanDiscriminationMemory = self.client.get_or_create_collection("booleanDiscriminationMemory",
                                                                           embedding_function=NexusEmbeddingFunction())
    if(self.booleanDiscriminationMemory.count() == 0):
      self.booleanDiscriminationMemory.add(documents=[negativeStr, positiveStr], ids=["0", "1"])
      
    self.closestWordMemory = self.client.get_or_create_collection("closestWordMemory",
                                                                  embedding_function=NexusEmbeddingFunction())
    if(self.closestWordMemory.count() == 0):
      with open("./models/vocab.txt", "r") as f:
        words = f.read().splitlines()
      words = list(filter(lambda s: not any(s.startswith(c) for c in invalidChars) and len(s)>2, words))
      ids = [f"id_{i}" for i in range(0, len(words))]
      self.closestWordMemory.add(documents=words, ids=ids)
      
    
  def CreateEpisodicMetadata(self, conversationId, role, proxy, entities, 
                           sentiment, tags, innerThoughts):
    timestamp = int(datetime.datetime.now())
    metadata={
            "conversationId": conversationId,
            "role": role,
            "proxy": proxy,
            "entities": entities,
            "sentiment": sentiment,
            "timestamp": timestamp,
            "innerThoughts": innerThoughts            
        }
    ########################################################################     call tag memory    
    return metadata    
  
  def CreateSimpleMetadata(self, conversationId, proxy, tags):
    timestamp = int(datetime.datetime.now())
    metadata=[
      {
       "conversationId": conversationId,
            "proxy": proxy,
            "timestamp": timestamp
      }
    ]
    ########################################################################     call tag memory    
    return metadata
  

  #I firmly refuse to use metadatas as a plural for metadata!!!!
  def CommitToMemory(self, memoryLevel, documents, metadata, ids):
    memoryLevel = self.client.get_or_create_collection(memoryLevel,
                                          embedding_function=NexusEmbeddingFunction())
    memoryLevel.upsert(documents=documents, metadatas=metadata, ids=ids)
    
 ######################################################## See below for updating metadata
  def UpdateMemoryMetadata(self, memoryLevel, query, metadata, maxRecords):
    memoryLevel = self.client.get_or_create_collection(memoryLevel,
                                          embedding_function=NexusEmbeddingFunction())
    ids = memoryLevel.query(where=query, n_results=maxRecords, include=[])
    metadataList = [metadata] * len(ids)
    
    memoryLevel.update(ids=ids, metadatas=metadataList)
    
  def Count(self, memoryLevel, where):
    memoryLevel = self.client.get_or_create_collection(memoryLevel,
                                          embedding_function=NexusEmbeddingFunction())
    ct = memoryLevel.count()
    query =memoryLevel.query(query_texts=[""], n_results=ct, where=where,include=[])
    ids = query["ids"][0]
    return len(ids)
  
  def getItemsByTreshold(query, threshold):
    ids = query["ids"][0]
    count = len(ids)
    list = []
    for i in range(count):
      if query["distances"][0][i] <= threshold:
        list.append({"id": ids[i], "distance": query["distances"][0][i]})
    return list    


  def TagMemory(self, proxy, tag):
    
    if(self.tagMemory.exists("tag")):
      entry = self.tagMemory.get("tag")
      tagConversations =entry.metadata.get("conversations", [])
      if(not proxy.context.contextID in tagConversations):
        tagConversations.append(proxy.context.contextID)
    
    self.tagMemory.update_metadata(
    entry_id=tag,
    metadata={"conversations": tagConversations},
    merge=True  # Set merge=True to merge the new metadata with the existing metadata
    )
    
  def GetRecollectionContext(self, maxSize=1024):
    if(self.recollectionContext):
      ctx = deque()
      self.recollectionContext.sort(key = lambda x : x.priority)
      ctx.extend(self.recollectionContext)
      
      while (sum(x.tokenSize for x in ctx) > maxSize):
        ctxSize += ctx[0].tokenSize
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
    
  def AddToRecollectionContext(self, text, priority, query):
    if((query not in self.recollectionQueries) and (text not in map(lambda x: x.text, self.recollectionContext))):
      self.recollectionQueries.append(text)
      tokenSize = globalNexus.GetTokenCount(text)    
      self.recollectionContext.append(tuple(text=text, priority= priority, tokenSize= tokenSize))
    
    
# tuple(text, priority: float,  tokenSize: int, contextID: str)       
    
    
globalMemory = Memory()    
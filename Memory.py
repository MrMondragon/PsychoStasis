from chromadb import PersistentClient
from Nexus import NexusEmbeddingFunction
import itertools
import datetime
import uuid

positive = ["yes", "sure", "ok", "okay", "yeah", "yup", "yep", "yea", "yah", "yas", "ya", "yap"]
negative = ["no", "nope", "nah", "nay", "nope", "nah", "nay"]
invalidChars = ["#", "@", "!", "$", "%", "^", "&", "*", "(", ")", "-", "_", "=", "+", "{", "}", "[", "]", "|", "\\", ":", ";", "'", "\"", "<", ">", ",", ".", "?", "/"]

positiveStr = " ".join(positive)
negativeStr = " ".join(negative)


class Memory(object):
  def __init__(self):
    self.path = './Memory/'
    self.client = PersistentClient(self.path)
    self.episodicMemory = self.client.get_or_create_collection("episodicMemory",
                                                               embedding_function=NexusEmbeddingFunction())
    self.factualMemory = self.client.get_or_create_collection("factualMemory",
                                                               embedding_function=NexusEmbeddingFunction())
    self.consolidatedMemory = self.client.get_or_create_collection("consolidatedMemory",
                                                                   embedding_function=NexusEmbeddingFunction())
    #raw text
    self.documentalMemoryLevel0 = self.client.get_or_create_collection("documentalMemoryLevel0",
                                                                       embedding_function=NexusEmbeddingFunction())
    #summarization level 1
    self.documentalMemoryLevel1 = self.client.get_or_create_collection("documentalMemoryLevel1",
                                                                       embedding_function=NexusEmbeddingFunction())
    #summarization level 2
    self.documentalMemoryLevel2 = self.client.get_or_create_collection("documentalMemoryLevel2",
                                                                       embedding_function=NexusEmbeddingFunction())
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
      
  def CreateEpisodicMemory(self, input, conversationId, entryId, role, proxy, entities, 
                           sentiment, tags):
    timestamp = int(datetime.datetime.now())
    documents=[input]
    metadata=[
        {
            "conversationId": conversationId,
            "role": role,
            "proxy": proxy,
            "entities": entities,
            "sentiment": sentiment,
            "tags": tags,
            "timestamp": timestamp,
            "id": entryId
        }
    ]
    return documents, metadata    
  
  def CreateFactualMemory(self, input, conversationId, entryId, role, proxy, sentiment, tags):
    timestamp = int(datetime.datetime.now())
    documents=[input]
    metadata=[
      {
       "conversationId": conversationId,
            "entryId": entryId,
            "role": role,
            "proxy": proxy,
            "sentiment": sentiment,
            "tags": tags,
            "timestamp": timestamp,
            "id": str(uuid.uuid4())
      }
    ]
    return documents, metadata    

  #I firmly refuse to use metadatas as a plural for metadata!!!!
  def CommitToMemory(self, memoryLevel, documents, metadata):
    memoryLevel = self.client.get_or_create_collection(memoryLevel,
                                          embedding_function=NexusEmbeddingFunction())
    memoryLevel.add(documents=documents, metadatas=metadata)
    
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

  def sentenceToBoolean(self, choice):
    query = self.booleanDiscriminationMemory.query(query_texts=[choice], n_results=1, where=[], include=[])
    id = query["ids"][0][0]
    if(id == "1"):
      return True
    else:
      return False
    
  def getClosestWord(self, sentence, top_k=1):
    query = self.closestWordMemory.query(query_texts=[sentence], 
                                         n_results=top_k, where=[], include=["documents"])
    word = query["documents"][0]
    return word
    
globalMemory = Memory()    
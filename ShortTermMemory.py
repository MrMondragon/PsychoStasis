from chromadb import Client
from Nexus import NexusEmbeddingFunction, globalNexus
from MemoryTypes import MemoryLevel, MemoryEntry
from LongTermMemory import longTermMemory
import itertools
from typing import Dict

basePriority = 500
windowSize = 320


class ShortTermMemory(object):
  def __init__(self):
    self.client = Client()
    self.attentionContext : Dict[str, MemoryEntry] = {}


  def ElicitMemory(self, text, proxy):
    globalNexus.BeginShardBatch("Embeddings.Embeddings")

    themes = longTermMemory.GetItemsByTreshold(proxy=proxy, memoryLevel=MemoryLevel.Thematic, threshold=1.4, queryText=text, where={"proxy":  { "$eq": proxy.name }})
    if(themes is None):
      return None
    
    factIds = [theme.metadata["factIds"] for theme in themes]
    factIds = "|".join(factIds)
    factIds = factIds.split("|")
    factIds = list(set(factIds))

    facts = longTermMemory.GetItemsByTreshold(proxy=proxy, memoryLevel=MemoryLevel.Abstract, threshold=0, queryText=text,
      where={
        "$and": [
            {"proxy": {"$eq": proxy.name}},
            {"id": {"$in": factIds}}
        ]
    })

    for fact in facts:
      fact.priority = basePriority

    sumIds = [fact.metadata["summaryIds"] for fact in facts]
    sumIds = "|".join(sumIds)
    sumIds = sumIds.split("|")
    sumIds = list(set(sumIds))

    summaries = longTermMemory.GetItemsByTreshold(proxy=proxy, memoryLevel=MemoryLevel.Summary, threshold=0, queryText=text,
      where={
        "$and": [
            {"proxy": {"$eq": proxy.name}},
            {"id": {"$in": sumIds}}
        ]
    })

    for sum in summaries:
      sum.priority = basePriority + 10

    epIds = [sum.metadata["episodes"] for sum in summaries]
    epIds = "|".join(epIds)
    epIds = epIds.split("|")
    epIds = list(set(epIds))

    episodes = longTermMemory.GetItemsByTreshold(proxy=proxy, memoryLevel=MemoryLevel.Episodic, threshold=0, queryText=text,
      where={
        "$and": [
            {"proxy": {"$eq": proxy.name}},
            {"id": {"$in": epIds}}
        ]
      }
    )

    for ep in episodes:
      ep.priority = basePriority + 20

    memoryContext = []
    memoryContext.extend(itertools.chain(facts, summaries, episodes))
    globalNexus.EndShardBatch("Embeddings.Embeddings")
    
    for memoryEntry in memoryContext:    
      if(memoryEntry.id in self.attentionContext):
        self.attentionContext[memoryEntry.id].priority = self.attentionContext[memoryEntry.id].priority - 10
      else:
        self.attentionContext[memoryEntry.id] = memoryEntry
    return memoryContext
        

  def PrioritizeMemory(self, text):
    workMemory = self.client.get_or_create_collection("workMemory", embedding_function=NexusEmbeddingFunction())
    self.client.delete_collection("workMemory")
    workMemory = self.client.get_or_create_collection("workMemory", embedding_function=NexusEmbeddingFunction())
    
    globalNexus.BeginShardBatch("Embeddings.Embeddings") 
    workMemory.add(documents=[memoryEntry.content for memoryEntry in self.attentionContext.values()], ids=[memoryEntry.id for memoryEntry in self.attentionContext.values()])
    
    query = workMemory.query(query_texts=[text], n_results=len(self.attentionContext.values()), include=['distances'])
    globalNexus.EndShardBatch("Embeddings.Embeddings") 
    
    ids = query["ids"][0]
    distances = query["distances"][0]
    
    for i in range(len(ids)):
      self.attentionContext[ids[i]].distance = distances[i]
      
    maxDistance = max(distances)
    for memoryEntry in self.attentionContext.values():
      memoryEntry.priority -= (1 - (memoryEntry.distance / (maxDistance/2))) * 15
    
    maxTimestamp = max([memoryEntry.timestamp for memoryEntry in self.attentionContext.values()])
    for memoryEntry in self.attentionContext.values():
      memoryEntry.priority -= (1 - (memoryEntry.timestamp / (maxTimestamp/2))) * 5
      
        
  def DiscardMemory(self):
    sortedMemories = sorted(self.attentionContext.values(), key=lambda memoryEntry: memoryEntry.priority)

    result = {}
    tokenCount = 0
    for entry in sortedMemories:
      if(tokenCount == 0):
        result[entry.id] = entry
        tokenCount+=entry.tokensSize
      else:
        tokenCount+=entry.tokensSize
        if tokenCount <= windowSize:
          result[entry.id] = entry
        else:
          break
        
    self.attentionContext = result
  
  
###############################################################
################# Short Term Memory Object ####################
###############################################################
shortTermMemory = ShortTermMemory()    
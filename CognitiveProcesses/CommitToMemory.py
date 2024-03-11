import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
sys.path.insert(0, str(Path(".")))
import uuid
from Memory import globalMemory
from Nexus import globalNexus
from _BaseCognitiveProcess import BaseCognitiveProcess
from Proxy import Proxy


class CommitToMemory(BaseCognitiveProcess):
  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.shouldRun = True
    self.Name = "CommitToMemory"
    self.Contexts = ["afterMessageReceived"] if "contexts" not in kwargs else kwargs["contexts"]
    self.Frequency = 10 if "frequency" not in kwargs else kwargs["frequency"]
    self.shouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.common = True
    
  def _internalRun(self):
    super()._internalRun()
    localContext = self.getLocalContext()
    if(localContext != []):
      texContext = "\n".join([message["content"] for message in localContext])
      entities = globalNexus.getNER(texContext)
      sentiment = globalNexus.getSentiment(texContext)
      conversationId=self.proxy.context.contextID
      documents = []
      ids = []
      metadata = []
      #Episodic memory --> full conversation
      for message in localContext:
        if(message["role"] == "assistant"):
          role = self.proxy.name
        else:
          role = message["role"]         
          data = globalMemory.CreateEpisodicMemory(input = message["content"],
                                                   conversationId=conversationId,
                                                   role=role,
                                                   proxy = self.proxy.name,
                                                   entities=entities,
                                                   sentiment=sentiment, 
                                                   tags=[])
        documents.append(message["content"])
        ids.append(message["id"])
        metadata.append(data)
      globalMemory.CommitToMemory(memoryLevel="episodicMemory", documents=documents, metadata=metadata, ids=ids)
      
      
      self.proxy.enterSubContext(copySystem=False, start=self.Frequency*-1)
      
      #facts about the conversation so far
      facts = self.proxy.GenerateAnswer(prompt="Cite three facts you can gather from this conversation. Do not introduce yourself. Answer with the files only!")
      facts = facts.splitlines()
      if(facts):
        if(len(facts) > 3):
          facts = facts[-3:]
        documents = []
        ids = []
        metadata = []      
        for fact in facts:
          data = globalMemory.CreateSimpleMemory(input = fact,
                                                 conversationId=conversationId,
                                                 proxy=self.proxy.name,
                                                 tags=[])
          documents.append(fact)
          ids.append(uuid.uuid4())
          metadata.append(data)
        globalMemory.CommitToMemory(memoryLevel="factualMemory", documents=documents, metadata=metadata, ids=ids)
      self.proxy.exitSubContext()
      
      #summary of the conversation so far, commited to the consolidated memory
      summary = globalNexus.summarize(texContext)
      data = globalMemory.CreateSimpleMemory(input = summary,
                                             conversationId=conversationId,
                                             proxy=self.proxy.name,
                                             tags=[])
      globalMemory.CommitToMemory(memoryLevel="consolidatedMemory", documents=[summary], metadata=[data], ids=[conversationId])
      
      
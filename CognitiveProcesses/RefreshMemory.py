import sys
from pathlib import Path
sys.path.insert(0, str(Path("..")))
sys.path.insert(0, str(Path(".")))
from ShortTermMemory import shortTermMemory
from _BaseCognitiveProcess import BaseCognitiveProcess

class RefreshMemory(BaseCognitiveProcess):
  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.shouldRun = True
    self.Name = "RefreshMemory"
    self.contexts = ["messageReceived"] if "contexts" not in kwargs else kwargs["contexts"]
    self.frequency = 0 if "frequency" not in kwargs else kwargs["frequency"] #10
    self.shouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.common = True
    self.priority = 100
    
  def _internalRun(self):
    super()._internalRun()
    text = self.proxy.context.lastMessageTxt
    ctx = shortTermMemory.ElicitMemory(text, self.proxy)
    if(ctx is None):
      return
    shortTermMemory.PrioritizeMemory(text)
    shortTermMemory.DiscardMemory()
    
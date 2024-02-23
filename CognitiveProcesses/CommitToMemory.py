
from BaseCognitiveProcess import BaseCognitiveProcess

class CommitToMemory(BaseCognitiveProcess):
  def __init__(self, name, **kwargs) -> None:
    super().__init__(name, **kwargs)
    
  def _internalRun(self, proxy):
    super()._internalRun(proxy)
    # add to episodic memory
    # update consolidated memory
    # try to extract facts
    
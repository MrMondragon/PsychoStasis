import sys
from MemoryTypes import MemoryLevel
from pathlib import Path
sys.path.insert(0, str(Path("..")))
sys.path.insert(0, str(Path(".")))
from ShortTermMemory import shortTermMemory
from _BaseCognitiveProcess import BaseCognitiveProcess
from Logger import globalLogger, LogLevel

class CharacterAlignment(BaseCognitiveProcess):
  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.shouldRun = True
    self.Name = "CharacterAlignment"
    self.contexts = ["messageReceived"] if "contexts" not in kwargs else kwargs["contexts"]
    self.frequency = 1 if "frequency" not in kwargs else kwargs["frequency"] #10
    self.shouldRun = True if "shouldRun" not in kwargs else kwargs["shouldRun"]
    self.common = False
    self.priority = 500
    
  def _internalRun(self):
    super()._internalRun()
    message = self.system.params["lastMessage"]
    self.proxy.enterSubContext(deepCopy=True, copySystem=True, innerThoughts=True)
    try:
      msg = f"{message}\n Respond in character. Be concise and to the thoughtful."
      globalLogger.log(logLevel=LogLevel.cognitiveLog, message=f"Altered message: {msg}")
      answer = self.proxy.GenerateAnswer(prompt=msg)
    finally:
      self.proxy.exitSubContext()
    self.proxy.context.AppendMessage(message, "user", self.proxy.context.userName)
    self.proxy.context.messageHistory.append(answer)
    self.proxy.context.lastAnswerObj = answer
    self.proxy.context.lastAnswerTxt = answer.content
    self.system.RunProcesses(proxy=self, context="afterMessageReceived")
    
    self.proxy.ShouldGenerate = False   
    
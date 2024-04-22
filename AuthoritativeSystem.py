from DynamicSystem import DynamicSystem
import re
from Logger import globalLogger, LogLevel
import traceback

class AuthoritativeSystem(DynamicSystem):

  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.Commands = {}
    self.RegisterCommands()
    
    
  def Run(self, proxy, prompt, role):
    command = ""
    try:
      if(re.match(r"\W", prompt)): #check if prompt is a command. Commands must ALWAYS start with \W, non word char
        if(prompt == "/help"):
          result = list(map(lambda x: x[0] + " :: " + x[1].description, self.Commands.items()))
          for item in result:
            globalLogger.log(message = item, logLevel = LogLevel.authoritativeLog)          
          return ""
        
        expressions = self.Commands.keys()
        for expression in expressions:
          command = re.match(expression, prompt)
          if(command):
            prompt = self.Commands[expression].func(proxy=proxy,prompt=prompt, command = command.group())
      return prompt
    except Exception as e:
      globalLogger.log(message = f"Error processing authoritative prompt {prompt}: {e}", logLevel = LogLevel.errorLog)
      globalLogger.log(message = traceback.format_exc(), logLevel = LogLevel.errorLog)
    
  def getProcessPath(self):
    return "AuthoritativeModules"
  
  def RegisterCommands(self):
    for process in self.processes.values():
      process.RegisterCommands(self)  
      
      
authoritativeSystem = AuthoritativeSystem()


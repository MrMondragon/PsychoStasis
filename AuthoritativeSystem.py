from DynamicSystem import DynamicSystem
import re

class AuthoritativeSystem(DynamicSystem):

  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.Commands = {}
    self.RegisterCommands()
    
    
  def Run(self, proxy, message, role):
    while(re.match(r"\W", message)): #check if message is a command. Commands must ALWAYS start with \W, non word char
      expressions = self.Commands.keys()
      for expression in expressions:
        command = re.match(expression, message)
        if(command):
          message = self.Commands[expression](proxy=proxy,prompt=message, command = command.group())
    return message
    
    
  def getProcessPath(self):
    return "/AuthoritativeModules/"
  
  def RegisterCommands(self):
    for process in self.processes:
      process.RegisterCommands()  
      
      
authoritativeSystem = AuthoritativeSystem()


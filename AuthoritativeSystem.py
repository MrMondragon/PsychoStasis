from DynamicSystem import DynamicSystem
import re

class AuthoritativeSystem(DynamicSystem):

  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)
    self.Commands = {}
    self.RegisterCommands()
    
    
  def Run(self, proxy, prompt, role):
    if(re.match(r"\W", prompt)): #check if prompt is a command. Commands must ALWAYS start with \W, non word char
      expressions = self.Commands.keys()
      for expression in expressions:
        command = re.match(expression, prompt)
        if(command):
          prompt = self.Commands[expression].func(proxy=proxy,prompt=prompt, command = command.group())
    return prompt
    
    
  def getProcessPath(self):
    return "AuthoritativeModules"
  
  def RegisterCommands(self):
    for process in self.processes.values():
      process.RegisterCommands(self)  
      
      
authoritativeSystem = AuthoritativeSystem()


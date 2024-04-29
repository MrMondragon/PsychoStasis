import datetime
from enum import Enum


class LogLevel(Enum):
  errorLog = 0
  globalLog = 1
  thoughtLog = 2
  authoritativeLog = 3
  cognitiveLog = 4
  uiLog = 5
  warningLog = 6
  
class LogEntry():
  def __init__(self, message, logLevel: LogLevel):
    self.message = message
    self.logLevel = logLevel
    self.logTime = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]

class Logger(object):
  def __init__(self):
    self.logEntries = []

  def log(self, message, logLevel: LogLevel):
    entry = LogEntry(message, logLevel)
    self.logEntries.append(entry)
    msg = f"[{entry.logTime}] {entry.logLevel.name}: {entry.message}"
    print(msg)
    return entry
    
  def GenerateHTML(self):
    if(self.logEntries == []):
      return ""
    
    html = ""
    currentLevel = ""
    for entry in self.logEntries:
      level=entry.logLevel.name
      
      if level != currentLevel:
        if(currentLevel != ""):
          html += "</details>"
        html += f"<details><summary class='{level}'>[{entry.logTime}] {level}</summary>"
        currentLevel = level
      
      html += f"<p class='{level} logEntry' >{entry.logTime}: {entry.message}</p>"
    
    html += "</details>"      
    return html
    

      
    
globalLogger = Logger()


import datetime


class Logger(object):
  def __init__(self, name):
    self.name = name
    self.logEntries = {}

  def log(self, message):
    logTime = datetime.datetime.now()
    self.logEntries[logTime] = message
    print(f"[{logTime}] {self.name}: {message}")
    
globalLogger = Logger("globalLogger")

class _Command(object):
  def __init__(self, **kwargs):
    self.func = kwargs["func"]
    self.description = kwargs["description"]
    
    
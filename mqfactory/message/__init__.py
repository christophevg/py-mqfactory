class Message(object):
  def __init__(self, to, payload):
    self.to      = to
    self.payload = payload
    self.tags    = {}

  def __iter__(self):
    yield ("to",      self.to)
    yield ("payload", self.payload)
    return

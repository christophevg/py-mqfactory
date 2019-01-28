class Message(object):
  def __init__(self, to, payload, tags=None):
    self.to      = to
    self.payload = payload
    self.tags    = tags or {}

  def __iter__(self):
    yield ("to",      self.to)
    yield ("payload", self.payload)
    return

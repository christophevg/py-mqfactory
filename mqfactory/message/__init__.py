import copy

class Message(object):
  def __init__(self, to, payload, tags=None):
    self.to      = to
    self.payload = payload
    self.tags    = tags or {}

  def copy(self):
    return Message(
      self.to,
      copy.deepcopy(self.payload),
      copy.deepcopy(self.tags)
    )

  def __iter__(self):
    yield ("to",      self.to)
    yield ("payload", self.payload)
    yield ("tags",    self.tags)
    return

  def __str__(self):
    return str(dict(self))

import copy
import uuid

class Message(object):
  def __init__(self, to, payload, tags=None, id=None):
    self.to         = to
    self.payload    = payload
    self.tags       = tags or {}
    self.private    = {}
    self.tags["id"] = id or str(uuid.uuid4())

  def copy(self):
    return Message(
      self.to,
      copy.deepcopy(self.payload),
      tags=copy.deepcopy(self.tags),
      id=self.tags["id"]
    )

  def __iter__(self):
    yield ("to",      self.to)
    yield ("payload", self.payload)
    yield ("tags",    self.tags)
    return

  def __str__(self):
    return str(dict(self))

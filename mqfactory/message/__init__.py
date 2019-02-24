import copy
import uuid

class Message(object):
  def __init__(self, to, payload, tags=None, id=None):
    self.to         = to
    self.payload    = payload
    self.tags       = tags or {}
    self.private    = {}
    self.tags["id"] = id or str(uuid.uuid4())

  @property
  def id(self):
    return self.tags["id"]

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
    return str({
      "to"     : self.to,
      "payload": self.payload,
      "tags"   : self.tags
    })

  def __eq__(self, other): 
    return self.to      == other.to \
       and self.payload == other.payload \
       and self.tags    == other.tags \
       and self.private == other.private

  def __ne__(self, other):
    return not self == other

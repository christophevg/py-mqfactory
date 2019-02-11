import logging

from mqfactory import millis

class Outbox(object):
  def __init__(self, mq=None, clock=None):
    self.mq            = mq
    self.clock         = clock or millis
    self.messages      = {}
    self.before_add    = []
    self.after_add     = []
    self.before_remove = []
    self.after_remove  = []
    self.before_defer  = []
    self.after_defer   = []
    self.before_get    = []

  def add(self, message):
    for handler in self.before_add:
      handler(self, message)
    self.messages[message.id] = message
    message.tags["last"] = self.clock()
    for handler in self.after_add:
      handler(self, message)

  def remove(self, message):
    for handler in self.before_remove:
      handler(self, message)
    del self.messages[message.id]
    for handler in self.after_remove:
      handler(self, message)
    return message

  def defer(self, message):
    for handler in self.before_defer:
      handler(self, message)
    message.tags["last"] = self.clock()
    for handler in self.after_defer:
      handler(self, message)
    return message

  def __len__(self):
    return len(self.messages)

  def __iter__(self):
    return self  # pragma: no cover
  
  def next(self):
    return self.__next__() # pragma: no cover
  
  def __next__(self):
    for handler in self.before_get:
      handler(self)
    if len(self.messages) < 1:
      raise StopIteration
    try:
      message = min(self.messages.values(),key=lambda msg: msg.tags["last"])
      return message
    except KeyError:
      logging.error("missing last tag : {0}".format(self.messages))
      raise StopIteration

  def __getitem__(self, id):
    message = self.messages[id]
    for handler in self.before_get:
      handler(self, message)
    return message

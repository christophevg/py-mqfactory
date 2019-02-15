import logging

from mqfactory import millis, wrap

class Queue(object):
  def __init__(self, mq=None, ticks=None):
    self.mq            = mq
    self.ticks         = ticks or millis
    self.messages      = {}
    self.before_add    = []
    self.after_add     = []
    self.before_remove = []
    self.after_remove  = []
    self.before_defer  = []
    self.after_defer   = []
    self.before_get    = []

  def add(self, message):
    wrap(message, self.before_add)
    self.messages[message.id] = message
    message.tags["last"] = self.ticks()
    wrap(message, self.after_add)    

  def remove(self, message):
    wrap(message, self.before_remove)
    del self.messages[message.id]
    wrap(message, self.after_remove)

  def defer(self, message):
    wrap(message, self.before_defer)
    message.tags["last"] = self.ticks()
    wrap(message, self.after_defer)

  def __len__(self):
    return len(self.messages)

  def __iter__(self):
    return self  # pragma: no cover
  
  def next(self):
    return self.__next__() # pragma: no cover
  
  def __next__(self):
    wrap(None, self.before_get)
    if len(self.messages) < 1:
      raise StopIteration
    message = min(self.messages.values(), key=lambda msg: msg.tags["last"])
    return message

  def __getitem__(self, id):
    message = self.messages[id]
    wrap(message, self.before_get)
    return message

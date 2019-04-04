import logging
from threading import RLock

from mqfactory.tools import clock, wrap

class Queue(object):
  def __init__(self, name="queue"):
    self.name          = name
    self.messages      = {}
    self.before_add    = []
    self.after_add     = []
    self.before_remove = []
    self.after_remove  = []
    self.before_defer  = []
    self.after_defer   = []
    self.before_get    = []
    self.lock = RLock()

  def add(self, message, wrapping=True):
    with self.lock:
      logging.info("queue[{0}]: add: {1}".format(self.name, message.id))
      if wrapping: wrap(message, self.before_add)
      self.messages[message.id] = message
      message.private["last"] = clock.now()
      if wrapping: wrap(message, self.after_add)    

  def remove(self, message):
    with self.lock:
      logging.info("queue[{0}]: remove: {1}".format(self.name, message.id))
      wrap(message, self.before_remove)
      del self.messages[message.id]
      wrap(message, self.after_remove)

  def defer(self, message):
    with self.lock:
      wrap(message, self.before_defer)
      message.private["last"] = clock.now()
      wrap(message, self.after_defer)

  def __len__(self):
    return len(self.messages)

  def __iter__(self):
    return self  # pragma: no cover
  
  def next(self):
    return self.__next__() # pragma: no cover
  
  def __next__(self):
    with self.lock:
      wrap(None, self.before_get)
      if len(self.messages) < 1:
        raise StopIteration
      message = min(self.messages.values(), key=lambda msg: msg.private["last"])
      return message

  def __getitem__(self, id):
    with self.lock:
      message = self.messages[id]
      wrap(message, self.before_get)
      return message

import logging

class Outbox(object):
  def __init__(self, mq=None):
    self.mq             = mq
    self.messages       = []
    self.before_append  = []
    self.after_append   = []
    self.before_pop     = []
    self.after_pop      = []
    self.before_defer   = []
    self.after_defer    = []
    self.before_getnext = []

  def append(self, message):
    for handler in self.before_append:
      message = handler(self, message)
    self.messages.append(message)
    for handler in self.after_append:
      message = handler(self)

  def pop(self, index=0):
    for handler in self.before_pop:
      handler(self, index)
    message = self.messages.pop(index)
    for handler in self.after_pop:
      handler(self, index, message)
    return message

  def defer(self, index=0):
    for handler in self.before_defer:
      handler(self, index)
    message = None
    try:
      message = self.messages.append(self.messages.pop(index))
      for handler in self.after_defer:
        handler(self)
    except IndexError:
      logging.warning("trying to defer message that now seems gone?")
    return message

  def index(self, matches):
    message = next((x for x in self.messages if matches(x)), [None])
    return self.messages.index(message)

  def __len__(self):
    return len(self.messages)

  def __iter__(self):
    return self
  
  def next(self):
    return self.__next__()
  
  def __next__(self):
    for handler in self.before_getnext:
      handler(self)
    try:
      return self.messages[0]
    except IndexError:
      raise StopIteration

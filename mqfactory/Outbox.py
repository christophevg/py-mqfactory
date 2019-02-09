class Outbox(object):
  def __init__(self, mq=None):
    self.mq             = mq
    self.items          = []
    self.before_append  = []
    self.after_append   = []
    self.before_pop     = []
    self.after_pop      = []
    self.before_defer   = []
    self.after_defer    = []
    self.before_getnext = []

  def append(self, item):
    for handler in self.before_append:
      item = handler(self, item)
    self.items.append(item)
    for handler in self.after_append:
      item = handler(self)

  def pop(self, index=0):
    for handler in self.before_pop:
      handler(self, index)
    item = self.items.pop(index)
    for handler in self.after_pop:
      handler(self, index, item)
    return item

  def defer(self, index=0):
    for handler in self.before_defer:
      handler(self, index)
    item = None
    try:
      item = self.items.append(self.items.pop(index))
      for handler in self.after_defer:
        handler(self)
    except IndexError:
      # TODO fix this race condition, when a defer of a retry is done while
      #      acknowledgement arrives and removes the item before this runs
      pass
    return item

  def index(self, matches):
    item = next((x for x in self.items if matches(x)), [None])
    return self.items.index(item)

  def __len__(self):
    return len(self.items)

  def __iter__(self):
    return self
  
  def next(self):
    return self.__next__()
  
  def __next__(self):
    for handler in self.before_getnext:
      handler(self)
    try:
      return self.items[0]
    except IndexError:
      raise StopIteration

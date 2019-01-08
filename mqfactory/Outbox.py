class Outbox(object):
  def __init__(self, mq=None):
    self.mq             = mq
    self.items          = []
    self.after_append   = []
    self.after_pop      = []
    self.after_setitem  = []
    self.before_append  = []
    self.before_pop     = []
    self.before_getitem = []

  def append(self, item):
    for handler in self.before_append:
      item = handler(self, item)
    self.items.append(item)
    for handler in self.after_append:
      item = handler(self, item)

  def pop(self, index=0):
    for handler in self.before_pop:
      (index, item) = handler(self, index, self.items[index])
    item = self.items.pop(index)
    for handler in self.after_pop:
      (index, item) = handler(self, index, item)
    return item

  def __len__(self):
    return len(self.items)

  def __getitem__(self, index):
    for handler in self.before_getitem:
      index = handler(self, index)
    return self.items[index]

  def __setitem__(self, index, new):
    old = self.items[index]
    self.items[index] = new
    for handler in self.after_setitem:
      handler(self, index, old, new)

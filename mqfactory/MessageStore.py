class MessageStore(object):
  def __init__(self, store):
    self.store = store
    self.loaded = False

  def persist(self, mq):
    mq.outbox.before_append.append(self.before_append)
    mq.outbox.after_append.append(self.after_append)

    mq.outbox.before_pop.append(self.before_pop)
    mq.outbox.after_pop.append(self.after_pop)

    mq.outbox.before_getitem.append(self.before_getitem)
    mq.outbox.after_setitem.append(self.after_setitem)
    return mq

  def before_append(self, outbox, item):
    self.load_items(outbox)
    return item

  def after_append(self, outbox, item):
    self.store.add(item)
    return item

  def before_pop(self, outbox, index, item):
    self.load_items(outbox)
    return (index, item)

  def after_pop(self, outbox, index, item):
    self.store.remove(item)
    return (index, item)
    
  def before_getitem(self, outbox, index):
    self.load_items(outbox)
    return index

  def after_setitem(self, outbox, index, old, new):
    self.store.update(new)
    return (index, old, new)

  def load_items(self, outbox):
    if not self.loaded:
      outbox.items = self.store.load()
      self.loaded = True

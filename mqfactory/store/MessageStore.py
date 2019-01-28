from mqfactory import Message

class MessageStore(object):
  def __init__(self, collection):
    self.collection = collection
    self.loaded = False

  def before_append(self, outbox, item):
    self.load_items(outbox)
    return item

  def after_append(self, outbox, item):
    item.tags["id"] = self.collection.add(dict(item))
    return item

  def before_pop(self, outbox, index, item):
    self.load_items(outbox)
    return (index, item)

  def after_pop(self, outbox, index, item):
    self.collection.remove(item.tags["id"])
    return (index, item)
    
  def before_getitem(self, outbox, index):
    self.load_items(outbox)
    return index

  def after_setitem(self, outbox, index, old, new):
    self.collection.update(old.tags["id"], dict(new))
    return (index, old, new)

  def load_items(self, outbox):
    if not self.loaded:
      for doc in self.collection.load():
        message = Message(doc["to"], doc["payload"])
        message.tags["id"] = doc["_id"]
        outbox.items.append(message)
      self.loaded = True

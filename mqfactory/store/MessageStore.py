from mqfactory import Message

class MessageStore(object):
  def __init__(self, collection):
    self.collection = collection
    self.loaded = False

  def before_append(self, outbox, item):
    self.load_items(outbox)
    return item

  def after_append(self, outbox):
    item = outbox.items[-1]
    item.tags["id"] = self.collection.add(dict(item))
    return item

  def before_pop(self, outbox, index):
    self.load_items(outbox)

  def after_pop(self, outbox, index, item):
    self.collection.remove(item.tags["id"])
    return (index, item)
    
  def before_getnext(self, outbox):
    self.load_items(outbox)

  def load_items(self, outbox):
    if not self.loaded:
      for doc in self.collection.load():
        message = Message(doc["to"], doc["payload"])
        message.tags["id"] = doc["_id"]
        outbox.items.append(message)
      self.loaded = True

from mqfactory.message import Message

class MessageStore(object):
  def __init__(self, collection):
    self.collection = collection
    self.loaded = False

  def before_append(self, outbox, message):
    self.load_messages(outbox)
    return message

  def after_append(self, outbox):
    message = outbox.messages[-1]
    message.private["id"] = self.collection.add(dict(message))
    return message

  def before_pop(self, outbox, index):
    self.load_messages(outbox)

  def after_pop(self, outbox, index, message):
    self.collection.remove(message.private["id"])
    return (index, message)
    
  def before_getnext(self, outbox):
    self.load_messages(outbox)

  def load_messages(self, outbox):
    if not self.loaded:
      for doc in self.collection.load():
        message = Message(doc["to"], doc["payload"])
        message.private["id"] = doc["_id"]
        outbox.messages.append(message)
      self.loaded = True

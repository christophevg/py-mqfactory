import logging

from mqfactory.message import Message

class MessageStore(object):
  def __init__(self, collection):
    self.collection = collection
    self.loaded = False

  def before_add(self, outbox, message):
    self.load_messages(outbox)

  def after_add(self, outbox, message):
    message.private["id"] = self.collection.add(dict(message))
    logging.debug("message {0} store as {1}".format(message.id, message.private["id"]))

  def before_remove(self, outbox, message):
    self.load_messages(outbox)

  def after_remove(self, outbox, message):
    self.collection.remove(message.private["id"])
    
  def before_get(self, outbox, message=None):
    self.load_messages(outbox)

  def after_defer(self, outbox, message):
    try:
      self.collection.update(message.private["id"], dict(message))
    except:
      logging.error("after_defer update failed for {0}".format(str(message)))

  def load_messages(self, outbox):
    if not self.loaded:
      for doc in self.collection.load():
        message = Message(doc["to"], doc["payload"], doc["tags"])
        message.private["id"] = doc["_id"]
        outbox.messages[message.id] = message
      self.loaded = True

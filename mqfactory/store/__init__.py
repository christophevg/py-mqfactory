import logging

from mqfactory.message import Message

class Store(object):
  def __getitem__(self, key):
    raise NotImplementedError("implement get collection from the store")

class Collection(object):
  def load(self):
    raise NotImplementedError("implement loading the collection")
    
  def __getitem__(self, key):
    raise NotImplementedError("implement get item from collection")

  def add(self, item):
    raise NotImplementedError("implement adding item to the collection")

  def remove(self, item):
    raise NotImplementedError("implement removing item from the collection")

  def update(self, key, item):
    raise NotImplementedError("implement updating item in the collection")

class MessageStore(object):
  def __init__(self, queue, collection):
    self.queue      = queue
    self.collection = collection
    self.loaded     = False

    self.queue.before_add.append(self.before_add)
    self.queue.after_add.append(self.after_add)
    self.queue.before_remove.append(self.before_remove)
    self.queue.after_remove.append(self.after_remove)
    self.queue.after_defer.append(self.after_defer)
    self.queue.before_get.append(self.before_get)

  def before_add(self, message):
    self.load_messages()

  def after_add(self, message):
    message.private["store-id"] = self.collection.add(dict(message))
    logging.debug("store: after_add: message {0} stored as {1}".format(
      message.id, message.private["store-id"]
    ))

  def before_remove(self, message):
    self.load_messages()

  def after_remove(self, message):
    self.collection.remove(message.private["store-id"])
    
  def before_get(self, message=None):
    self.load_messages()

  def after_defer(self, message):
    try:
      self.collection.update(message.private["store-id"], dict(message))
    except Exception as e:
      logging.error("store: after_defer: update failed for {0}: {1}".format(
        str(message), str(e)
      ))

  def load_messages(self):
    if not self.loaded:
      logging.info("loading messages...")
      for doc in self.collection.load():
        message = Message(doc["to"], doc["payload"], doc["tags"])
        message.private["store-id"] = doc["_id"]
        self.queue.add(message, wrapping=False)
      self.loaded = True
      logging.info("loaded")

def Persisting(mq, outbox=None, inbox=None):
  if outbox: MessageStore(mq.outbox, outbox)
  if inbox:  MessageStore(mq.inbox,  inbox)
  return mq

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
  def __init__(self, mq, collection):
    self.mq         = mq
    self.collection = collection
    self.loaded     = False

  def before_add(self, message):
    self.load_messages()

  def after_add(self, message):
    message.private["id"] = self.collection.add(dict(message))
    logging.debug("message {0} store as {1}".format(message.id, message.private["id"]))

  def before_remove(self, message):
    self.load_messages()

  def after_remove(self, message):
    self.collection.remove(message.private["id"])
    
  def before_get(self, message=None):
    self.load_messages()

  def after_defer(self, message):
    try:
      self.collection.update(message.private["id"], dict(message))
    except:
      logging.error("after_defer update failed for {0}".format(str(message)))

  def load_messages(self):
    if not self.loaded:
      for doc in self.collection.load():
        message = Message(doc["to"], doc["payload"], doc["tags"])
        message.private["id"] = doc["_id"]
        self.queue.messages[message.id] = message
      self.loaded = True

def Persisting(mq, into=Collection()):
  store = MessageStore(mq, into)

  mq.outbox.before_add.append(store.before_add)
  mq.outbox.after_add.append(store.after_add)

  mq.outbox.before_remove.append(store.before_remove)
  mq.outbox.after_remove.append(store.after_remove)
  
  mq.outbox.after_defer.append(store.after_defer)
  
  mq.outbox.before_get.append(store.before_get)

  # TODO implement inbox persistence

  return mq

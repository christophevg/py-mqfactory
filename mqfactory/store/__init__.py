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

from mqfactory.store.MessageStore import MessageStore

def Persisting(mq, into=Collection()):
  store = MessageStore(into)

  mq.outbox.before_add.append(store.before_add)
  mq.outbox.after_add.append(store.after_add)

  mq.outbox.before_remove.append(store.before_remove)
  mq.outbox.after_remove.append(store.after_remove)
  
  mq.outbox.after_defer.append(store.after_defer)
  
  mq.outbox.before_get.append(store.before_get)

  return mq

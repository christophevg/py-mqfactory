class Store(object):
  def __getitem__(self, key):
    raise NotImplementedError("implement get collection from the store")

class Collection(object):
  def load(self):
    raise NotImplementedError("implement loading the collection")
  
  def add(self, item):
    raise NotImplementedError("implement adding item to the collection")

  def remove(self, id):
    raise NotImplementedError("implement removing item from the collection")

  def update(self, id, item):
    raise NotImplementedError("implement updating item in the store")

from mqfactory.store.MessageStore import MessageStore

def Persisting(mq, into=Collection()):
  store = MessageStore(into)

  mq.outbox.before_append.append(store.before_append)
  mq.outbox.after_append.append(store.after_append)

  mq.outbox.before_pop.append(store.before_pop)
  mq.outbox.after_pop.append(store.after_pop)

  mq.outbox.before_getitem.append(store.before_getitem)
  mq.outbox.after_setitem.append(store.after_setitem)

  return mq

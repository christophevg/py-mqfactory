class Store(object):
  def __getitem__(self, key):
    raise NotImplementedError("implement get collection from the store")

class Collection(object):
  def load(self):
    raise NotImplementedError("implement loading the collection")
  
  def add(self, item):
    raise NotImplementedError("implement adding item to the collection")

  def remove(self, item):
    raise NotImplementedError("implement removing item from the collection")

  def update(self, item):
    raise NotImplementedError("implement updating item in the store")

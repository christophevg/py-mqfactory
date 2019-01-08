class Store(object):
  def load(self, item):
    raise NotImplementedError("please implement loading items from the store")
  
  def add(self, item):
    raise NotImplementedError("please implement adding item to the store")

  def remove(self, item):
    raise NotImplementedError("please implement removing item from the store")

  def update(self, item):
    raise NotImplementedError("please implement updating item in the store")

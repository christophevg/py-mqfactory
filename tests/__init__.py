from mqfactory.store import Store

class TransportMock(object):
  def __init__(self):
    self.items  = []
    self.routes = {}
  
  def send(self, to, payload):
    self.items.append((to, payload))

  def on_message(self, to, handler):
    self.routes[to] = handler

  def deliver(self):
    for (to, payload) in self.items:
      self.routes[to](self, to, payload)

class StoreMock(Store):
  def __init__(self, items=[]):
    self.changelog = []
    self.items = items
  
  def load(self):
    self.changelog.append("load")
    return self.items

  def add(self, item):
    self.changelog.append(("add", item))

  def remove(self, item):
    self.changelog.append(("remove", item))
    
  def update(self, item):
    self.changelog.append(("update", item))

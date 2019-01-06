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

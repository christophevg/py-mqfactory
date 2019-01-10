class Transport(object):
  def connect(self):
    raise NotImplementedError("implement connecting to the transport")

  def disconnect(self):
    raise NotImplementedError("implement disconnecting from the transport")
    
  def send(self, to, payload):
    raise NotImplementedError("implement sending using transport")

  def on_message(self, to, handler):
    raise NotImplementedError("implement message callback registration")

import logging

class Transport(object):
  def __init__(self):
    self.before_sending  = []
    self.after_receiving = []

  def connect(self):
    raise NotImplementedError("implement connecting to the transport")

  def disconnect(self):
    raise NotImplementedError("implement disconnecting from the transport")

  def send(self, message):
    message = message.copy()
    for wrapper in self.before_sending:
      wrapper(message)
    logging.debug("sending: {0}".format(message))
    self._send(message)

  def _send(self, message):
    raise NotImplementedError("implement sending using transport")

  def on_message(self, to, handler):
    def wrapped_handler(message):
      for wrapper in self.after_receiving[::-1]:
        wrapper(message)
      handler(message)
    self._on_message(to, wrapped_handler)

  def _on_message(self, to, handler):
    raise NotImplementedError("implement message callback registration")

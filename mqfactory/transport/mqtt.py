try:
  from urllib.parse import urlparse
except ImportError:
  from urlparse import urlparse

import paho.mqtt.client as mqtt

from mqfactory.transport import Transport

class MQTTTransport(Transport):
  def __init__(self, uri, paho=None, id="", qos=0):
    self.client = paho or mqtt.Client()
    self.client.reinitialize(client_id=id)
    self.id     = id
    self.qos    = qos
    self.client.on_connect    = self.handle_on_connect
    self.client.on_disconnect = self.handle_on_disconnect

    self.config = urlparse(uri)
    if self.config.username and self.config.password:
      self.client.username_pw_set(self.config.username, self.config.password)
    self.connected = False
    self.subscriptions = []

  def handle_on_connect(self, client, id, flags, rc):
    if rc == 0:
      self.connected = True
      for (sub, callback) in self.subscriptions:
        self.client.message_callback_add(sub, callback)

  def handle_on_disconnect(self,):
    self.connected = False

  def connect(self):
    self.client.connect(self.config.hostname, self.config.port)
    self.client.loop_start()

  def disconnect(self):
    self.client.disconnect()
  
  def send(self, to, payload):
    assert self.connected
    self.client.publish(to, payload, self.qos)

  def on_message(self, to, handler):
    self.subscriptions.append((to, handler))
    if self.connected:
      self.client.message_callback_add(to, payload)

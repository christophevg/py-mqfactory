import pytest

from mqfactory.transport.mqtt import MQTTTransport

from . import PahoMock

def create_transport(uri="mqtt://localmock:1883", id="", qos=0):
  paho = PahoMock()
  transport = MQTTTransport(uri, paho=paho, id=id, qos=qos)
  return (paho, transport)

def test_client_id():
  (paho, transport) = create_transport(id="test")
  assert paho.client_id == "test"

def test_connection_and_disconnection():
  (paho, transport) = create_transport("mqtt://localmock:1883")
  assert not paho.connected
  assert not transport.connected
  transport.connect()
  assert paho.connected
  assert paho.hostname == "localmock"
  assert paho.port == 1883
  assert paho.loop_started
  assert transport.connected
  transport.disconnect()
  assert not transport.connected
  assert not paho.connected

def test_subscription_on_connect():
  (paho, transport) = create_transport()
  def receive(client, data, message):
    pass
  transport.on_message("to", receive)
  assert len(paho.handlers) == 0
  transport.connect()
  assert len(paho.handlers) == 1
  assert paho.handlers["to"] == receive

def test_send_fails_before_connect(message):
  (paho, transport) = create_transport()
  with pytest.raises(AssertionError):
    transport.send(*message)

def test_sending(message):
  (paho, transport) = create_transport()
  transport.connect()
  transport.send(*message)
  assert len(paho.queue) == 1
  assert paho.queue[0] == tuple(message) + (0, False)

def test_sending_with_qos(message):
  (paho, transport) = create_transport(qos=1)
  transport.connect()
  transport.send(*message)
  assert len(paho.queue) == 1
  assert paho.queue[0] == tuple(message) + (1, False)

def test_delivery(message):
  (paho, transport) = create_transport(qos=1)
  received = []
  def receive(client, data, message):
    received.append((client, data, message))
  transport.on_message(message.to, receive)
  transport.connect()
  paho.queue.append(tuple(message) + (0, False))
  paho.deliver()
  assert len(received) == 1
  assert received[0][0] == paho
  assert received[0][1] == None
  assert received[0][2].topic == message.to 
  assert received[0][2].payload == message.payload 

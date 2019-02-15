import pytest

from mqfactory.transport.mqtt import MQTTTransport

from .conftest import PahoMessageMock

def test_client_id(paho):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho, id="test")
  assert paho.client_id == "test"

def test_connection_and_disconnection(paho):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho)
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

def test_subscription_on_connect(paho, message):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho)
  received = []
  def receive(msg):
    received.append(msg)
  transport.on_message(message.to, receive)
  assert len(paho.handlers) == 0
  transport.connect()
  assert len(paho.handlers) == 1
  # execute the handler (which is wrapped) to see its ours underneath
  assert len(received) == 0
  paho.handlers[message.to](
    None, None, PahoMessageMock(message.to, message.payload)
  )
  assert len(received) == 1
  assert received[0].to == message.to
  assert received[0].payload == message.payload

def test_send_fails_before_connect(paho, message):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho)
  with pytest.raises(AssertionError):
    transport.send(message)

def test_sending(paho, message):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho)
  transport.connect()
  transport.send(message)
  assert len(paho.queue) == 1
  assert paho.queue[0] == (message.to, message.payload, 0, False)

def test_sending_with_qos(paho, message):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho, qos=1)
  transport.connect()
  transport.send(message)
  assert len(paho.queue) == 1
  assert paho.queue[0] == (message.to, message.payload, 1, False)

def test_delivery(paho, message):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho)
  received = []
  def receive(msg):
    received.append(msg)
  transport.on_message(message.to, receive)
  transport.connect()
  paho.queue.append((message.to, message.payload, 0, False))
  paho.deliver()
  assert len(received) == 1
  assert received[0].to == message.to 
  assert received[0].payload == message.payload 

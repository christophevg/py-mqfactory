import pytest
from mock import Mock

from mqfactory.transport.mqtt import MQTTTransport

def test_client_id(paho):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho, id="test")
  paho.reinitialise.assert_called_with(client_id="test")

def test_connection_and_disconnection(paho):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho)

  transport.connect()
  paho.connect.assert_called_with("localmock", 1883)
  paho.loop_start.assert_called()

  transport.disconnect()
  paho.disconnect.assert_called()

def test_subscription_on_connect(paho, message, paho_message):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho)
  receive = Mock()
  transport.on_message(message.to, receive)
  transport.connect()
  assert paho.on_connect == transport.handle_on_connect
  transport.handle_on_connect(None, None, None, 0)
  paho.subscribe.assert_called_with(message.to)
  paho.message_callback_add.assert_called()
  (args, _) = paho.message_callback_add.call_args
  (sub, wrapped_callback) = args
  assert sub == message.to
  wrapped_callback(None, None, paho_message)
  receive.assert_called()
  (args, _) = receive.call_args
  msg = args[0]
  assert msg.to == message.to
  assert msg.payload == message.payload

def test_send_fails_before_connect(paho, message):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho)
  with pytest.raises(AssertionError):
    transport.send(message)

def test_sending(paho, message):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho)
  transport.connect()
  transport.handle_on_connect(None, None, None, 0)
  transport.send(message)
  paho.publish.assert_called_with(message.to, message.payload, 0)

def test_sending_with_qos(paho, message):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho, qos=1)
  transport.connect()
  transport.handle_on_connect(None, None, None, 0)
  transport.send(message)
  paho.publish.assert_called_with(message.to, message.payload, 1)

def test_sending_raises_exception_when_disconnected(paho, message):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho)
  transport.connect()
  transport.handle_on_connect(None, None, None, 0)
  transport.handle_on_disconnect()
  with pytest.raises(AssertionError):
    transport.send(message)

def test_subscription_when_connected(paho, message, paho_message):
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho)
  receive = Mock()
  transport.connect()
  transport.handle_on_connect(None, None, None, 0)
  transport.on_message(message.to, receive)
  paho.subscribe.assert_called_with(message.to)
  paho.message_callback_add.assert_called()

def test_authenticated_connection(paho):
  transport = MQTTTransport("mqtt://user:pass@localmock:1883", paho=paho)
  paho.username_pw_set.assert_called_with("user", "pass")

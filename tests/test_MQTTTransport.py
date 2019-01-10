from mqfactory.transport.mqtt import MQTTTransport

from . import PahoMock

def test_client_id():
  paho = PahoMock()
  transport = MQTTTransport("mqtt://localmock:1883", paho=paho, id="test")
  assert paho.client_id == "test"

# TODO

import pytest

import random
import string
import copy
import logging

from mqfactory.message   import Message
from mqfactory.transport import Transport
from mqfactory.store     import Store, Collection

def generate_random_string(length=10):
  return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

@pytest.fixture
def ids():
  def generator():
    generator.id += 1
    return generator.id
  generator.id = 0
  return generator

@pytest.fixture
def ticks():
  def generator():
    generator.id += 1
    return generator.id
  generator.id = 0
  return generator

@pytest.fixture
def message():
  to      = generate_random_string()
  payload = generate_random_string()
  tags    = {}
  id      = generate_random_string()
  return Message(to, payload, tags, id)

class TransportMock(Transport):
  def __init__(self):
    super(TransportMock, self).__init__()
    self.items  = []
    self.routes = {}
    self.log    = []

  def connect(self):
    pass

  def disconnect(self):
    pass
  
  def _send(self, msg):
    self.items.append(msg)

  def _on_message(self, to, handler):
    self.routes[to] = handler

  def deliver(self):
    while len(self.items) > 0:
      message = self.items.pop(0)
      self.log.append((message.to, message.payload))
      try:
        self.routes[message.to](message)
      except KeyError:
        logging.warning("no handler for route {0}".format(message.to))

  def deliver_direct(self, to, payload):
    self.routes[to](Message(to, payload))

@pytest.fixture
def transport():
  return TransportMock()

class StoreMock(Store):
  def __init__(self, collections={}):
    self.collections = {}
    for collection in collections:
      self.collections[collection] = CollectionMock(collections[collection])

  def __getitem__(self, key):
    if not key in self.collections:
      self.collections[key] = CollectionMock()
    return self.collections[key]

class CollectionMock(Collection):
  def __init__(self, items=None):
    self.changelog = []
    self.items = items or {}
  
  def load(self):
    self.changelog.append("load")
    return self.items.values()

  def __getitem__(self, key):
    return self.items[key]

  def add(self, item):
    if "_id" in item:
      id = item["_id"]
    else:
      id = str(len(self.changelog))
    self.items[id] = item
    self.changelog.append(("add", id, copy.deepcopy(dict(item))))
    return id

  def remove(self, id):
    self.changelog.append(("remove", id))
    self.items.pop(id)

  def update(self, id, item):
    self.changelog.append(("update", id, copy.deepcopy(dict(item))))
    self.items[id] = item

@pytest.fixture
def store():
  return StoreMock({ "collection": {} })

@pytest.fixture
def collection(store):
  return store["collection"]

class PahoMock(object):
  on_connect    = None
  on_subscribe  = None
  on_message    = None
  on_disconnect = None
  
  def __init__(self, client_id="", clean_session=True, userdata=None,
                     protocol="MQTTv311", transport="tcp"):
    self.client_id    = client_id
    self.username     = None
    self.password     = None
    self.will_topic   = None
    self.will_payload = None
    self.will_qos     = 0
    self.will_reain   = False
    self.hostname     = None
    self.port         = None
    self.handlers     = {}
    self.queue        = []
    self.connected    = False
    self.loop_started = False

  def reinitialise(self, client_id="", clean_session=True, userdata=None, 
                         protocol="MQTTv311", transport="tcp"):
    self.client_id = client_id

  def username_pw_set(self, username, password):
    self.username = username
    self.password = password

  def will_set(self, topic, payload=None, qos=0, retain=False):
    self.will_topic   = topic
    self.will_payload = payload
    self.will_qos     = qos
    self.will_reatin  = retain

  def connect(self, hostname, port):
    self.hostname = hostname
    self.port     = port
    self.on_connect(self, self.client_id, [], 0)
    self.connected = True

  def loop_start(self):
    self.loop_started = True

  def message_callback_add(self, topic, handler):
    self.handlers[topic] = handler

  def subscribe(self, topic):
    return (0, 0)

  def publish(self, topic, payload, qos=0, retain=False):
    self.queue.append((topic, payload, qos, retain))

  def disconnect(self):
    self.on_disconnect()
    self.connected = False
    self.loop_started = False

  def deliver(self):
    for item in self.queue:
      self.handlers[item[0]](self, None, PahoMessageMock(item[0], item[1]))

class PahoMessageMock(object):
  def __init__(self, topic, payload):
    self.topic   = topic
    self.payload = payload

@pytest.fixture
def paho():
  return PahoMock()

class SignatureMock(object):
  def __init__(self, signature=generate_random_string()):
    self.signature = signature

  def sign(self, item):
    item.tags["signature"] = self.signature

  def validate(self, item):
    assert item.tags["signature"] == self.signature

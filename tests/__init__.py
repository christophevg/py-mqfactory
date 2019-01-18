from mqfactory.transport import Transport
from mqfactory.store     import Store, Collection

class TransportMock(Transport):
  def __init__(self):
    self.items  = []
    self.routes = {}

  def connect(self):
    pass

  def disconnect(self):
    pass
  
  def send(self, msg):
    self.items.append(msg)

  def on_message(self, to, handler):
    self.routes[to] = handler

  def deliver(self):
    for message in self.items:
      self.routes[message.to](message)

class StoreMock(Store):
  def __init__(self, collections={}):
    self.collections = {}
    for collection in collections:
      self.collections[collection] = CollectionMock(collections[collection])

  def __getitem__(self, key):
    return self.collections[key]

class CollectionMock(Collection):
  def __init__(self, items=[]):
    self.changelog = []
    self.items = items
  
  def load(self):
    self.changelog.append("load")
    return self.items

  def add(self, item):
    id = len(self.changelog)
    self.changelog.append(("add", id, dict(item)))
    return id

  def remove(self, id):
    self.changelog.append(("remove", int(id)))
    
  def update(self, id, item):
    self.changelog.append(("update", int(id), dict(item) ))


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

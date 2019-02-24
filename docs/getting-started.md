# Getting Started

The following example shows the capabilities I needed when I started implementing this: 

- MongoDB-based persistency
- ... of messages sent by means of an MQTT message broker
- ... with RSA-based public/private-key-based signatures
- ... and acknowledgment with retries after a fixed timeout.

The following steps allow you to see these requirements in action:

Install a local instance of MongoDB and the Mosquitto MQTT broker. On macOS with brew installed, your minimal survival commands are:

```bash
$ brew install mongodb
$ brew services start mongodb
$ brew install mosquitto
$ brew services start mosquitto
```

Create a folder with a virtual Python environment:

```bash
$ mkdir demo
$ cd demo
$ virtualenv venv
$ . venv/bin/activate
(venv) $ pip install mqfactory
```

> TIP: if you want to work from the repository you can also use pip to install mqfactory: `pip install /path/to/cloned/repository/mqfactory`

Create a file `demo.py` containing:

```python
import time
import socket

# The core of the factory allows for instantiating a `MessageQueue`. Such an MQ
# has an inbox and an outbox, which can be processed using the `process_inbox`
# and `process_outbox` methods (or the `send_and_receive` method). To automate
# this we can apply `Threaded` to the MQ to automate calling these methods.
from mqfactory                      import Threaded, MessageQueue

# An MQ needs at least a way to send its message, this is a `Transport`. Here we
# use an MQTT implementation.
from mqfactory.transport.mqtt       import MQTTTransport

# One aspect of transporting messages is how much care is taken in making sure
# they are delivered. This is often called quality of service and can take many
# forms. Here we choose to retry sending messages untill they are acknowledged.
from mqfactory.transport.qos        import Acknowledging

# An MQ takes any payload and will pass it as-is. Here we choose to have the 
# payload formatted using JSON, taking care of serializing and deserializing.
from mqfactory.message.format.js    import JsonFormatting

# A standard MQ will hold its messages in a `Queue` in memory. Using a
# `Collection` in a `Store` we can persist these, e.g. to a `MongoStore`.
from mqfactory.store                import Persisting
from mqfactory.store.mongo          import MongoStore

# Let's use a localy running MongoDB instance:
mongo = MongoStore("mongodb://localhost:27017/mqfactory")

# Beside formatting it using JSON, we also choose to have our payload signed and
# validated using a public/private keypair. Keys for these signatures are also
# storable in a `Collection` in a `Store`, such as the `MongoStore`.
from mqfactory.message.security     import Signing
from mqfactory.message.security.rsa import RsaSignature

# Since we want to sign our messages, we need to provision a keypair.
from mqfactory.message.security.rsa import generate_key_pair, encode
private, public = generate_key_pair()

# We store the keypair in a MongoDB collection(keys) and identify the pair by
# our hostname, which is the default used by MQFactory.
HOSTNAME = socket.gethostname()
mongo["keys"].remove(HOSTNAME)
mongo["keys"].add({
  "_id": HOSTNAME,
  "private": encode(private),
  "public" : encode(public)
})

# Now we can finally assemble all these components into our own specific MQ,
# adding layer after layer:

mq = JsonFormatting(
       Signing(
         Acknowledging(
           Persisting(
             Threaded(
               MessageQueue(
                 MQTTTransport("mqtt://localhost:1883")
               )
             ),
             inbox=mongo["inbox"],
             outbox=mongo["outbox"]
           )
         ),
         adding=RsaSignature(mongo["keys"])
       )
     )

# When receiving a message, just print it to the console...

def show(msg):
  print "received {0} from {1}, tagged with {2}".format(
    msg.payload, msg.to, msg.tags
  )

# Subscribe to incoming messages addressed to myself and handle them with show.

mq.on_message("myself", show)

# Finally, send a message ... to myself.

mq.send("myself", "a message")

time.sleep(1) # to make sure we receive the answer ;-)
```

> TIP: if you are working from the repository, the `demo.py` example is also available:
```
$ git clone https://github.com/christophevg/mqfactory
$ cd mqfactory/example
$ virtualenv venv
$ . venv/bin/activate
(venv) $ pip install ../
```

Now in a separate terminal setup a mosquitto subscription:

```bash
$ mosquitto_sub -v -t '#'
```

Optionally, you can also monitor your MongoDB using [mongotail](https://github.com/mrsarm/mongotail):

```bash
$ pip install mongotail
$ mongotail mqfactory -l 2
Profiling level set to level 2
$ mongotail mqfactory -f
```

And run the demo script:

```bash
(venv) $ python demo.py 
received a message from myself, tagged with {u'ack': u'mq/ack', u'id': u'a93f159d-25de-4035-86c0-3d4964efbfe0'}
```

The mosquitto subscription shows the messages as they passes through the broker:

- the actual message, with acknowledge request and signature
- the acknowledgement, confirming to the original message, also with a signature

```bash
$ mosquitto_sub -v -t '#'
myself {"payload": "a message", "tags": {"ack": "mq/ack", "id": "a93f159d-25de-4035-86c0-3d4964efbfe0", "signature": {"hash": "foY/tqaAr74ZkC+stGTzz7xQMz0XFgRh9SET2evxqz+DfldYBXAMfQ0Ly35TR4BMcLWQNxDc5FR2BJYN7Xruv8PxlJwLZy+oU3Zzx3iPmaoJrSQdoEQqtfQSaBloAcfuBAYdXq36iM5ebPpewy5sy1K5Ei3hHU1RSwWTA3erDOPun/Z37GBar5LmuwNdg7Di7XEaty+dIHBTPGntIWw5FLK8RJTfhT63QHgKAQ07dfeuC9ewqCfK1bLJkSOfa0j/67ERT3vub+9p28JsfpGeU4v68Y16htHVAtTgl2GL/Edu1Ka6qVwqCvtr+vrWkGwKGNIdTe+KvbeDeNSn7E04IQ==", "origin": "kibo.local", "ts": "2019-02-24 14:32:22.500375"}}}
mq/ack {"payload": {}, "tags": {"confirm": "a93f159d-25de-4035-86c0-3d4964efbfe0", "id": "75e5d47b-9058-467b-a8fc-044b8d1f5631", "signature": {"hash": "uDwrYswNQVkWw6S4/PozhPScswZpz3GBcVTb40UYFRNXaL2BendXRjCbh2X7vscveugL5xyXrZRHvUKTm27ic2DDqLUzKvxxWYrB18UFNRL4iUKuP6VAACWLgCipcF527gCGD0qTxb5dtM8beYDSDKkUO7sChtQwiFg1yfhyPaZR9EZZtg3nEwifFv7VCu3QMHiZlF10zdKF7dVjSXKgQimscE5+9bqjDxj2eliDnnIo2BKLSt20VhtoXgeEfjUN/fuYcaIsNTfkghHsWBKda8oXD/DOSxgERlNElXjDnvHUh1t/DuS6EXClqLImC2kwvuUVM4neXXVfIY3f/d3U6Q==", "origin": "kibo.local", "ts": "2019-02-24 14:32:22.514979"}}}
```

The MongoDB logging will show the following activity:

```bash
$ mongotail mqfactory -f
2019-02-24 14:32:22.467 REMOVE    [keys] : {"_id": "kibo.local"}. 1 deleted.
2019-02-24 14:32:22.468 INSERT    [keys] : 1 inserted.
2019-02-24 14:32:22.473 QUERY     [keys] : {"_id": "kibo.local"}. 1 returned.
2019-02-24 14:32:22.474 QUERY     [outbox] : {}. 0 returned.
2019-02-24 14:32:22.475 INSERT    [outbox] : 1 inserted.
2019-02-24 14:32:22.505 UPDATE    [outbox] : {"_id": ObjectId("5c72aaf6e4e2adbde46e7600")}, {"$set": {"to": "myself", "payload": "a message", "tags": {"ack": "mq/ack", "id": "a93f159d-25de-4035-86c0-3d4964efbfe0", "sent": 1551018742502, "signature": {"origin": "kibo.local", "hash": "foY/tqaAr74ZkC+stGTzz7xQMz0XFgRh9SET2evxqz+DfldYBXAMfQ0Ly35TR4BMcLWQNxDc5FR2BJYN7Xruv8PxlJwLZy+oU3Zzx3iPmaoJrSQdoEQqtfQSaBloAcfuBAYdXq36iM5ebPpewy5sy1K5Ei3hHU1RSwWTA3erDOPun/Z37GBar5LmuwNdg7Di7XEaty+dIHBTPGntIWw5FLK8RJTfhT63QHgKAQ07dfeuC9ewqCfK1bLJkSOfa0j/67ERT3vub+9p28JsfpGeU4v68Y16htHVAtTgl2GL/Edu1Ka6qVwqCvtr+vrWkGwKGNIdTe+KvbeDeNSn7E04IQ==", "ts": "2019-02-24 14:32:22.500375"}}}}. 1 updated.
2019-02-24 14:32:22.507 QUERY     [inbox] : {}. 0 returned.
2019-02-24 14:32:22.507 INSERT    [inbox] : 1 inserted.
2019-02-24 14:32:22.508 QUERY     [keys] : {"_id": "kibo.local"}. 1 returned.
2019-02-24 14:32:22.509 INSERT    [outbox] : 1 inserted.
2019-02-24 14:32:22.510 REMOVE    [inbox] : {"_id": ObjectId("5c72aaf6e4e2adbde46e7601")}. 1 deleted.
2019-02-24 14:32:22.512 UPDATE    [outbox] : {"_id": ObjectId("5c72aaf6e4e2adbde46e7600")}, {"$set": {"to": "myself", "payload": "a message", "tags": {"ack": "mq/ack", "id": "a93f159d-25de-4035-86c0-3d4964efbfe0", "sent": 1551018742502, "signature": {"origin": "kibo.local", "hash": "foY/tqaAr74ZkC+stGTzz7xQMz0XFgRh9SET2evxqz+DfldYBXAMfQ0Ly35TR4BMcLWQNxDc5FR2BJYN7Xruv8PxlJwLZy+oU3Zzx3iPmaoJrSQdoEQqtfQSaBloAcfuBAYdXq36iM5ebPpewy5sy1K5Ei3hHU1RSwWTA3erDOPun/Z37GBar5LmuwNdg7Di7XEaty+dIHBTPGntIWw5FLK8RJTfhT63QHgKAQ07dfeuC9ewqCfK1bLJkSOfa0j/67ERT3vub+9p28JsfpGeU4v68Y16htHVAtTgl2GL/Edu1Ka6qVwqCvtr+vrWkGwKGNIdTe+KvbeDeNSn7E04IQ==", "ts": "2019-02-24 14:32:22.500375"}}}}. 1 updated.
2019-02-24 14:32:22.516 REMOVE    [outbox] : {"_id": ObjectId("5c72aaf6e4e2adbde46e7602")}. 1 deleted.
2019-02-24 14:32:22.517 INSERT    [inbox] : 1 inserted.
2019-02-24 14:32:22.518 QUERY     [keys] : {"_id": "kibo.local"}. 1 returned.
2019-02-24 14:32:22.519 REMOVE    [outbox] : {"_id": ObjectId("5c72aaf6e4e2adbde46e7600")}. 1 deleted.
2019-02-24 14:32:22.519 REMOVE    [inbox] : {"_id": ObjectId("5c72aaf6e4e2adbde46e7603")}. 1 deleted.
```

First some setup:

- the removal of optional previous keys (1 in this case, from a previous test) and the provisioning of a fresh key pair
- the retrieval of the key pair to fetch the private key to sign with
- a query to load any previous outgoing messages (0 in this case)

Then the actual sending of the message:

- an insertion for the message we want to send
- an update due to actually sending the message, including the signature

The message arrives and...

- a query to load any previous incoming messages not yet processed (0 in this case)
- an insertion for the message that arrived
- a query to fetch the public key is performed to validate the signature
- an acknowledging message is created in the outbox
- after handling, the message is removed from the inbox
- the original message in the outbox is updated. This is due to it being checked for resends; this will be improved upon soon ;-)
- the acknowledgement in the outbox is processed and removed

Finally the acknowledgement arrives and...

- it is inserted in the inbox
- a query to fetch the public key is performed to validate the signature
- the original/pending message, awaiting acknowledgment, is removed
- and the incoming acknowledgement is removed

> WARNING: This demo is sending messages to itself. In a real world situation, the in- and outboxes are shared between sender and receiver. For a demo, this makes the demo code a bit easier on the eye. Trust me, this could lead to ugly race conditions and bugs ;-)

If you are running from the repository, you can also try an other example with two communicating MessageQueues: `speed.py`:

```
(venv) $ python speed
Speed: 85 msg/s (468, 468, 11) 
```

Each queue responds to an incoming message, by sending a message back. This goes back and forth. The number of messages processed by each queue is counted and a "speed" indication is reported.

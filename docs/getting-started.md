# Getting Started

The following example shows the capabilities I needed when I started implementing this. I needed: 

- MongoDB-based persistency
- for an MQTT message broker
- (with RSA-based public/private-key-based signatures)
- (and acknowledgment with retries after a fixed timeout.)

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

Create a file `demo.py` containing:

```python
import time
import socket

# The core of the factory allows for instantiating a `MessageQueue`. Such an MQ
# has an outbox, which can be processed using the `process_outbox` method. To
# automate this we can apply `Threaded` to the MQ to automate calling this
# method.
from mqfactory                      import Threaded, MessageQueue

# An MQ needs at least a way to send its message, this is a `Transport`. Here we
# select the MQTT implementation.
from mqfactory.transport.mqtt       import MQTTTransport

# One aspect of transporting messages is how much care is taken in making sure
# they are delivered. This is often called quality of service and can take many
# forms. Here we choose to retry sending messages untill they are acknowledged.
from mqfactory.transport.qos        import Acknowledging

# An MQ takes any payload and will pass it as-is. Here we choose to have the 
# payload formatted using JSON, taking care of serializing and deserializing.
from mqfactory.message.format.js    import JsonFormatting

# A standard MQ will hold its messages in an `Outbox` in memory. Using a
# `Collection` in a `Store` we can persist these, e.g. to a `MongoStore`.
from mqfactory.store                import Persisting
from mqfactory.store.mongo          import MongoStore

# Beside formatting it using JSON, we also choose to have our payload signed and
# validated using a public/private keypair. Keys for these signatures are also
# storable in a `Collection` in a `Store`, such as the `MongoStore`.
from mqfactory.message.security     import Signing
from mqfactory.message.security.rsa import RsaSignature

# we need to provision a keypair
from mqfactory.message.security.rsa import generate_key_pair, encode
private, public = generate_key_pair()

# We can now assemble all these components into our own specific MQ:

mongo = MongoStore("mongodb://localhost:27017/mqfactory")

HOSTNAME = socket.gethostname()

mongo["keys"].remove(HOSTNAME)
mongo["keys"].add({
  "_id": HOSTNAME,
  "private": encode(private),
  "public" : encode(public)
})

mq = JsonFormatting(
       Signing(
         Acknowledging(
           Persisting(
             Threaded(
               MessageQueue(
                 MQTTTransport("mqtt://localhost:1883")
               )
             ),
             into=mongo["messages"]
           )
         ),
         adding=RsaSignature(mongo["keys"])
       )
     )

# and use it to send and receive messages

def show(msg):
  print "received {0} from {1}, tagged with {2}".format(
    msg.payload, msg.to, msg.tags
  )

mq.on_message("myself", show)

mq.send("myself", "a message")

time.sleep(3) # to make sure we receive the answer
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
received a message from myself, tagged with {u'ack': {u'to': u'/ack', u'id': u'c8e122e8-0686-4555-9850-01b747f3831b'}, u'id': u'5c5f263de4e2ad806ec7615b'}
```

The mosquitto subscription shows the message as it passes through the broker:

```bash
myself {"payload": "a message", "tags": {"ack": {"id": "c8e122e8-0686-4555-9850-01b747f3831b", "to": "/ack"}, "id": "5c5f263de4e2ad806ec7615b", "signature": {"hash": "K99vUO9/v6GuMX3tzV7QyKM/wKr6Qr0rb01jf1Q4N0M2p9YbWL8C54NU4YyHfXsDRrTFchlvqv5bhOui33YASJXU6AU/B2J5rWAs5KfbLVkGXj/VXWVbzdXvD3Lw6dehtGtTM9ZA+gDkj+pt5aDNqZ5es8mysB2TqpqMLF6iI9aMjLuPyv2iQ1QpOO+5BBU/zEkmL3dh1cdwks52wvtr6qMxrjVWbOynaevqTs0GXdYEQIRh602SFMIBOo08xxY6ukrFCxOHxEcBZS1UfpHASahx26Jmgj6YrCfehF18r3FDmi1Pq+2n7OBWeicHwFUa6y39gs+BATypwROBfucCKw==", "origin": "kibo.local", "ts": "2019-02-09 19:13:02.050718"}}}
/ack {"payload": {}, "tags": {"ack": {"id": "c8e122e8-0686-4555-9850-01b747f3831b"}, "id": "5c5f263ee4e2ad806ec7615d", "signature": {"hash": "2a78BDhdb39QEoDW+Xv/IuRcGw/ovNrKK50+vBaA9jHG/1LMdqoa/L7ANoVsVJh/1mLzg+tXzP0cuFFAL4JezQzMAh5siqW7WAV+rCYwajFB23Y0zT9l7jC805F+CD99ugkePI0cfPujivRNR6ti1Q+jVmkk0hGdZR+r9dDemlm1n72nlqrzEAPxyY4u6tU1gJk5AJudTDbjlHkFpgRuvD7qqrmty1nv1PgdADRrPBcSb0JJ+NDkhlkZN7u8a8+/hpzyfBe69SEpQgZFnjfCqdDFF8Oh+beKe8v1AKg6EQcaJs92cIn/weojSAlMAAQhV8uB4uJ2Xfi+WqTZjp77Iw==", "origin": "kibo.local", "ts": "2019-02-09 19:13:02.260316"}}}
```

The MongoDB logging will show the following activity:

```bash
2019-02-09 19:13:01.895 REMOVE    [keys] : {"_id": "kibo.local"}. 0 deleted.
2019-02-09 19:13:01.941 INSERT    [keys] : 1 inserted.
2019-02-09 19:13:01.946 QUERY     [keys] : {"_id": "kibo.local"}. 1 returned.
2019-02-09 19:13:01.947 QUERY     [messages] : {}. 0 returned.
2019-02-09 19:13:01.987 INSERT    [messages] : 1 inserted.
2019-02-09 19:13:02.055 INSERT    [messages] : 1 inserted.
2019-02-09 19:13:02.057 QUERY     [keys] : {"_id": "kibo.local"}. 1 returned.
2019-02-09 19:13:02.058 INSERT    [messages] : 1 inserted.
2019-02-09 19:13:02.059 REMOVE    [messages] : {"_id": ObjectId("5c5f263de4e2ad806ec7615b")}. 1 deleted.
2019-02-09 19:13:02.264 REMOVE    [messages] : {"_id": ObjectId("5c5f263ee4e2ad806ec7615d")}. 1 deleted.
2019-02-09 19:13:02.265 QUERY     [keys] : {"_id": "kibo.local"}. 1 returned.
2019-02-09 19:13:02.267 REMOVE    [messages] : {"_id": ObjectId("5c5f263ee4e2ad806ec7615c")}. 1 deleted.
```

First some setup:

- the removal of optional previous keys and the provisioning of a fresh key pair
- the retrieval of the key pair to fetch the private key to sign with
- a query to load any previous messages (0 in this case)

Then the actual sending of the message:

- an insertion for the message we want to send
- and an insertion for the scheduled retry

The message arrives and...

- a query to fetch the public key is performed to validate the signature
- an acknowledging message is created
- the original message is removed (this is a delayed action that should have happened at the end of the sending of the message)
- the (sent) acknowledgement is removed

Finally the acknowledgement arrives and...

- a query to fetch the public key is performed to validate the signature
- the pending retry message is now also removed

Every aspect (almost technically literally) is an implementation of an interface, so adding a different store, transport, signing procedure, retry strategy, requires a rather small implementation of such an interface.

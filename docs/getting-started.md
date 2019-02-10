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
received a message from myself, tagged with {u'ack': {u'to': u'/ack', u'id': u'cb4cbc1a-87da-4220-a7c0-1ed935d5852f'}}
```

The mosquitto subscription shows the messages as they passes through the broker:

- the actual message, with acknowledge request and signature
- the acknowledgement, referring to the original message and also with a signature

```bash
myself {"payload": "a message", "tags": {"ack": {"id": "cb4cbc1a-87da-4220-a7c0-1ed935d5852f", "to": "/ack"}, "signature": {"hash": "mOxtp1SegeDbnNElqsvvRbV9sSs+oRyhHwHe05KyTsyRcI8dQ89xJXU6+TqdQhOZMupFC7TDZf8OXbfHVZVajpsiDc488spGtRI8YI34+SnSlbk/CkGhCW58OevpJYR4Oh08eAczW+ZfKDiEbg7qEQuNGdDABlzjR4V78B/mKpvT2qbmgpAlGx2xCm+eQPOVrmOTpBOqvotZBZEyc8+quaR/U+VwYA7+4D3HJfuiDgtiCF2iCkIv71Wx7bqxGquZqOomTqFGwHe1DLPaqII/DSNwl4hKXRUcNZpavcoYLtGxGBdjfMM45iVm1NqXGS9FTTtZyOIHRF8cYeU/EGfzeA==", "origin": "kibo.local", "ts": "2019-02-10 10:13:07.309281"}}}
/ack {"payload": {}, "tags": {"ack": {"id": "cb4cbc1a-87da-4220-a7c0-1ed935d5852f"}, "signature": {"hash": "GJwEanfzsIds1SnhTeav/LHvDuTTLqzYafeb3Gpru2NLuNIsHgVbuGmJpVhbk7NEjBVLbonqtSSWqluuFhWkQj+fdg9i/5lfzI0AfmAZ0LqP8XslbJuYpNYCopbWORcxUn0yus5VXP5RZimRbfc5uc1MwFRlXQaJNjM0pYTEyyky+UTWpTWZZwDBPL8E+nXQmCPqLgHNGfpWaSM760j7FZbfggVMP/R4yr4HqYPDQqa7VtFMrOzGHFdpI563Go2CpdKqN89W4HmNijDliZt+z+a3IUqU5L81f/y1uzsp18CfHXk4IS13F0/EGwgrupYs28hFpaz9m3nds4aXhLJLLA==", "origin": "kibo.local", "ts": "2019-02-10 10:13:07.515296"}}}
```

The MongoDB logging will show the following activity:

```bash
2019-02-10 10:13:07.302 REMOVE    [keys] : {"_id": "kibo.local"}. 0 deleted.
2019-02-10 10:13:07.303 INSERT    [keys] : 1 inserted.
2019-02-10 10:13:07.307 QUERY     [keys] : {"_id": "kibo.local"}. 1 returned.
2019-02-10 10:13:07.308 QUERY     [messages] : {}. 0 returned.
2019-02-10 10:13:07.309 INSERT    [messages] : 1 inserted.
2019-02-10 10:13:07.311 INSERT    [messages] : 1 inserted.
2019-02-10 10:13:07.311 QUERY     [keys] : {"_id": "kibo.local"}. 1 returned.
2019-02-10 10:13:07.312 REMOVE    [messages] : {"_id": ObjectId("5c5ff933e4e2ad8f1efd49f0")}. 1 deleted.
2019-02-10 10:13:07.313 INSERT    [messages] : 1 inserted.
2019-02-10 10:13:07.519 REMOVE    [messages] : {"_id": ObjectId("5c5ff933e4e2ad8f1efd49f2")}. 1 deleted.
2019-02-10 10:13:07.520 QUERY     [keys] : {"_id": "kibo.local"}. 1 returned.
2019-02-10 10:13:07.521 REMOVE    [messages] : {"_id": ObjectId("5c5ff933e4e2ad8f1efd49f1")}. 1 deleted.
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
- the original message is removed (this is a delayed action that should have happened at the end of the sending of the message)
- an acknowledging message is created
- the (sent) acknowledgement is removed

Finally the acknowledgement arrives and...

- a query to fetch the public key is performed to validate the signature
- the pending retry message is now also removed

Every aspect (almost technically literally) is an implementation of an interface, so adding a different store, transport, signing procedure, retry strategy, requires a rather small implementation of such an interface.

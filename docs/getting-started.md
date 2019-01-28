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
from mqfactory                   import Threaded, MessageQueue

# An MQ needs at least a way to send its message, this is a `Transport`. Here we
# select the MQTT implementation.
from mqfactory.transport.mqtt       import MQTTTransport

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
         Persisting(
           Threaded(
             MessageQueue(
               MQTTTransport("mqtt://localhost:1883")
             )
           ),
           into=mongo["messages"]
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

time.sleep(1) # to make sure we receive the answer
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
received a message from myself, tagged with {u'id': u'5c4f71dae4e2ada18a52e96b'}
```

The mosquitto subscription shows the message as it passes through the broker:

```bash
myself {"payload": "a message", "tags": {"id": "5c4f71dae4e2ada18a52e96b", "signature": {"origin": "kibo.local", "hash": "hivMJjPPvZUoiryvY4xVXt5jrxdvzlxgQ2wHjZZ3vybxCoY/TUs5R9EHnbP12FbOuekB+imRLg+JGgZ1XglIZ4O3B2Z6Kiy5wu+g3bxVVDcvqKmCDOjp7nteZafr7ni8i1fOuYVpTjjswViRhZGB7ousg+cmZrxv03SDfe87BZCuomi2e/PeFlIm099F67ijwMZzAjM1JQe7u/JJt/1/avCnfteDqWQrvHDsT9lpTckRQOWfW3ZLHf08VhDsy7jO766TE24Ex8+jHdZ+sVuiFie6HDkXMjwM4V2KaMYsuml6Jvovng9/gm3MWM5hjQJvGL7XO9KAgHMhUee2IA3qYA==", "ts": "2019-01-28 21:19:22.955222"}}}
```

Notice the `id` tag that is sent along. This is the ObjectId given to the message by the MongoDB. This is a nice side effect from using persistency, which requires messages to be given a unique identifier.

The MongoDB logging will show three queries on the messages collection due to an attempt to load existing messages from the `messages` collection, an insert of the message we want to send and a removal after successful sending. On the keys collection, we first see the inserting of the provisioned key pair and two queries, one for the private key when signing and one for getting the public key while validating.

```bash
2019-01-28 21:19:22.847 INSERT    [keys] : 1 inserted.
2019-01-28 21:19:22.850 QUERY     [keys] : {"_id": "kibo.local"}. 1 returned.
2019-01-28 21:19:22.851 QUERY     [messages] : {}. 0 returned.
2019-01-28 21:19:22.852 INSERT    [messages] : 1 inserted.
2019-01-28 21:19:22.959 REMOVE    [messages] : {"_id": ObjectId("5c4f71dae4e2ada18a52e96b")}. 1 deleted.
2019-01-28 21:19:22.965 QUERY     [keys] : {"_id": "kibo.local"}. 1 returned.
```

Every aspect (almost technically literally) is an implementation of an interface, so adding a different store, transport, signing procedure, retry strategy, requires a rather small implementation of such an interface.

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

# The core of the factory allows for instantiating a `MessageQueue`. Such an MQ
# has an outbox, which can be processed using the `process_outbox` method. To
# automate this we can apply `Threaded` to the MQ to automate calling this
# method.
from mqfactory                   import Threaded, MessageQueue

# An MQ needs at least a way to send its message, this is a `Transport`. Here we
# select the MQTT implementation.
from mqfactory.transport.mqtt    import MQTTTransport

# An MQ takes any payload and will pass it as-is. Here we choose to have the 
# payload formatted using JSON, taking care of serializing and deserializing.
from mqfactory.message.format.js import JsonFormatting

# A standard MQ will hold its messages in an `Outbox` in memory. Using a
# `Collection` in a `Store` we can persist these, e.g. to a `MongoStore`.
from mqfactory.store             import Persisting
from mqfactory.store.mongo       import MongoStore

# We can now assemble all these components into our own specific MQ:

mongo = MongoStore("mongodb://localhost:27017/mqfactory")

mq = JsonFormatting(
       Persisting(
         Threaded(
           MessageQueue(
             MQTTTransport("mqtt://localhost:1883")
           )
         ),
         into=mongo["messages"]
       )
     )

# and use to send and receive messages

def show(msg):
  print "received {0} from {1}".format(msg.payload, msg.to)

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
$ python demo.py 
received a message from myself
```

The mosquitto subscription shows the message that passes through the broker:

```bash
myself {"payload": "a message", "tags": {"id": "5c41d8e0e4e2ad4390362304"}}
```

Notice the `id` tag that is sent along. This is the ObjectId given to the message by the MongoDB. This is a nice side effect from using persistency, which requires messages to be given a unique identifier.

The MongoDB logging will show three queries due to an attempt to load existing messages from the `messages` collection, an insert of the message we want to send and a removal after successful sending:

```bash
2019-01-18 21:20:12.643 QUERY     [messages] : {}. 0 returned.
2019-01-18 21:20:12.644 INSERT    [messages] : 1 inserted.
2019-01-18 21:20:12.748 REMOVE    [messages] : {"_id": ObjectId("5c41d8e0e4e2ad4390362304")}. 1 deleted.
```

Every aspect (almost technically literally) is an implementation of an interface, so adding a different store, transport, signing procedure, retry strategy, requires a rather small implementation of such an interface.

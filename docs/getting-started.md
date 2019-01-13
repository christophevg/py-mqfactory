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
(venv) $ pip install py-mqfactory
```

Create a file `demo.py` containing:

```python
import time

# The core of the factory allows for instantiating a `MessageQueue`. Such an MQ
# has an outbox, which can be processed using the `process_outbox` method. To
# automate this we can apply `Threaded` to the MQ to automate calling this
# method.
from mqfactory                     import Threaded, MessageQueue

# An MQ needs at least a way to send its message, this is a `Transport`. Here we
# select the MQTT implementation.
from mqfactory.transport.mqtt      import MQTTTransport

# A standard MQ will hold its messages in an `Outbox` in memory. Using a
# `Collection` in a `Store` we can persist these, e.g. to a `MongoStore`.
from mqfactory.store               import Persisting
from mqfactory.store.mongo         import MongoStore

# We can now assemble all these components into our own specific MQ:

mongo = MongoStore("mongodb://localhost:27017/mqfactory")

mq = Persisting(
       Threaded(
         MessageQueue(
           MQTTTransport("mqtt://localhost:1883")
         )
       ),
       into=mongo["messages"]
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

And run the demo script:

```bash
$ python demo.py 
received a message from myself
```

The mosquitto subscription shows the message that passes through the broker:

```bash
myself a message
```

Every aspect (almost technically literally) is an implementation of an interface, so adding a different store, transport, signing procedure, retry strategy, requires a rather small implementation of such an interface.

# Getting Started

The following example shows the capabilities I needed when I started implementing this. I needed: 

- MongoDB-based persistency
- for an MQTT message broker
- with RSA-based public/private-key-based signatures
- and acknowledgment with retries after a fixed timeout.

```bash
$ pip install mqfactory
$ python
Python 2.7.15 (default, Dec 27 2018, 11:55:59) 
[GCC 4.2.1 Compatible Apple LLVM 10.0.0 (clang-1000.11.45.5)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> from mqfactory.store     import MongoStore
>>> from mqfactory.transport import MQTTTransport
>>> from mqfactory.security  import Signing
>>> from mqfactory           import Threaded, MessageQueue
>>> from mqfactory           import MessageStore, KeyStore
>>> mongo     = MongoStore( "mongodb://localhost:27017/mqfactory" )
>>> transport = MQTTTransport("mqtt://localhost:1883")
>>> mq        = Threaded(MessageQueue(transport))
>>> MessageStore(mongo["messages"]).persist(mq)
>>> KeyStore(mongo["keys"]).sign(mq)
```

Every aspect (almost technically literally) is an implementation of an interface, so adding a different store, transport, signing procedure, retry strategy, requires a rather small implementation of such an interface.

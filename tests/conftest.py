import copy
import pytest

from mqfactory.message import Message

from . import generate_random_string
from . import TransportMock, StoreMock

@pytest.fixture
def message():
  to      = generate_random_string()
  payload = generate_random_string()
  tags    = {}
  id      = generate_random_string()
  return Message(to, payload, tags, id)

@pytest.fixture
def transport():
  return TransportMock()

@pytest.fixture
def store():
  return StoreMock({ "collection": {} })

@pytest.fixture
def collection(store):
  return store["collection"]

@pytest.fixture
def id_generator():
  def generator():
    generator.id += 1
    return generator.id
  generator.id = 0
  return generator

@pytest.fixture
def clock():
  def generator():
    generator.id += 1
    return generator.id
  generator.id = 0
  return generator

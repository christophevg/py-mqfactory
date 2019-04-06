from mqfactory.tools import Policy, Rule, CATCH_ALL

def test_empty_policy():
  p = Policy()
  assert p.match({"something": "something"}) == CATCH_ALL
  assert p.match({}) == CATCH_ALL

def test_policy():
  p = Policy([
    Rule({ "a": 1,    "b": 1,    "c": 1 }, "a=1,b=1,c=1" ),
    Rule({ "a": 1,    "b": 1,           }, "a=1,b=1" ),
    Rule({ "a": 1,                      }, "a=1" ),
    Rule({            "b": 1,           }, "b=1" ),
  ])
  assert p.match({"a": 1}).value == "a=1"
  assert p.match({"b": 1}).value == "b=1"
  assert p.match({"a": 2, "b": 1, "c": 1}).value == "b=1"
  assert p.match({"a": 1, "b": 1, "c": 1}).value == "a=1,b=1,c=1"
  assert p.match({"a": 2, "b": 2, "c": 2}).value is None
  assert p.match({"d": 1}).value is None

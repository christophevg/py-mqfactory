class Signature(object):
  policy = None

  def __init__(self, policy=None):
    self.policy = policy

  def sign(self, message, *args, **kwargs):
    if self.policy is None or self.policy.match(dict(message)).value is None:
      return self._sign(message, *args, **kwargs)
    return False

  def _sign(self, message):
    raise NotImplementedError("implement signing of message")

  def validate(self, message, *args, **kwargs):
    if self.policy is None or self.policy.match(dict(message)).value is None:
      return self._validate(message, *args, **kwargs)
    return False

  def _validate(self, message):
    raise NotImplementedError("implement validation of message")

def Signing(mq, adding=Signature(), policy=None):
  if policy: adding.policy = policy
  mq.before_sending.append(adding.sign)
  mq.before_handling.append(adding.validate)
  return mq

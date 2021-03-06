# MQ Factory

> A framework for building message queues using Python

[![](https://img.shields.io/pypi/v/mqfactory.svg)](https://pypi.python.org/pypi/mqfactory/)
[![](https://img.shields.io/pypi/pyversions/mqfactory.svg)](https://pypi.python.org/pypi/mqfactory/)
[![](https://secure.travis-ci.org/christophevg/py-mqfactory.svg?branch=master)](http://travis-ci.org/christophevg/py-mqfactory)
[![](https://readthedocs.org/projects/mqfactory/badge/?version=latest)](https://mqfactory.readthedocs.io/en/latest/?badge=latest)
[![](https://coveralls.io/repos/github/christophevg/py-mqfactory/badge.svg?branch=master)](https://coveralls.io/github/christophevg/py-mqfactory?branch=master)
[![](https://img.shields.io/badge/PyPi_Template-v0.0.6-blue.svg)](https://github.com/christophevg/pypi-template)

```eval_rst
.. warning:: **Work in Progress** - I've only just started working on this and I'm literally exploring my own code as I write it ;-) So until this warning is removed, I wouldn't trust myself using this ;-) Do play with it, but remember things can and will change overnight.
```

## Rationale

I needed a Persistent Message Queue endpoint on top of an MQTT client, with message acknowledgement, timeouts, retries and signing & validation using a public/private keypair. A quick search delivered [persist-queue](https://github.com/peter-wangxu/persist-queue), which seemed to cover most what I was looking for. But after implementing part of my requirements, I hit some bumps in the road. To work around them I would almost have to implement the entire solution, so little added value was still to be found in reusing the existing module. Starting from scratch also allowed me to explore a few new things and introduce some other ideas.

After a first rough implementation, specific for my original use case, I felt that it was hard to test it nicely as-is. Breaking it down in several very composable components, allowed for vastly improved unit tests and in the end resulted in a nice reusable module.

## Contents

* [What is in the Box](whats-in-the-box.md)
* [Getting Started](getting-started.md)
* [Extending MQ Factory](extending.md)
* [Contributing](contributing.md)


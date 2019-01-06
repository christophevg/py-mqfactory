# MQ Factory

> A framework for building message queues using Python

[![Latest Version on PyPI](https://img.shields.io/pypi/v/mqfactory.svg)](https://pypi.python.org/pypi/mqfactory/)
[![Build Status](https://secure.travis-ci.org/christophevg/py-mqfactory.svg?branch=master)](http://travis-ci.org/christophevg/py-mqfactory)
[![Documentation Status](https://readthedocs.org/projects/mqfactory/badge/?version=latest)](https://mqfactory.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/christophevg/py-mqfactory/badge.svg?branch=master)](https://coveralls.io/github/christophevg/py-mqfactory?branch=master)
[![Built with PyPi Template](https://img.shields.io/badge/PyPi_Template-v0.0.5-blue.svg)](https://github.com/christophevg/pypi-template)

## Rationale

I needed a Persistent Message Queue endpoint on top of an MQTT client, with acknowledgement, timeouts and retries. A quick search delivered [persist-queue](https://github.com/peter-wangxu/persist-queue), which seemed to cover most what I was looking for. But after implementing part of my requirements, I hit some bumps in the road, and to work around them, I would almost implement the entire solution, so little added value was still to be found in reusing the existing module.

After a first rough implementation, specific for my use case, I felt that it was hard to test it nicely as-is. Breaking it down in several very compasable components, allowed for vastly improved unit tests and in the end resulted in a nice reusable module.

## Documentation

Visit [Read the Docs](https://mqfactory.readthedocs.org) for the full documentation, including overviews and several other examples.

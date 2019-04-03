# MQ Factory

> A framework for building message queues using Python

[![Latest Version on PyPI](https://img.shields.io/pypi/v/mqfactory.svg)](https://pypi.python.org/pypi/mqfactory/)
[![Supported Implementations](https://img.shields.io/pypi/pyversions/mqfactory.svg)](https://pypi.python.org/pypi/mqfactory/)
[![Build Status](https://secure.travis-ci.org/christophevg/py-mqfactory.svg?branch=master)](http://travis-ci.org/christophevg/py-mqfactory)
[![Documentation Status](https://readthedocs.org/projects/mqfactory/badge/?version=latest)](https://mqfactory.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/christophevg/py-mqfactory/badge.svg?branch=master)](https://coveralls.io/github/christophevg/py-mqfactory?branch=master)
[![Built with PyPi Template](https://img.shields.io/badge/PyPi_Template-v0.0.6-blue.svg)](https://github.com/christophevg/pypi-template)

## Rationale

I needed a Persistent Message Queue endpoint on top of an MQTT client, with message acknowledgement, timeouts, retries and signing & validation using a public/private keypair. A quick search delivered [persist-queue](https://github.com/peter-wangxu/persist-queue), which seemed to cover most what I was looking for. But after implementing part of my requirements, I hit some bumps in the road. To work around them I would almost have to implement the entire solution, so little added value was still to be found in reusing the existing module. Starting from scratch also allowed me to explore a few new things and introduce some other ideas.

After a first rough implementation, specific for my original use case, I felt that it was hard to test it nicely as-is. Breaking it down in several very composable components, allowed for vastly improved unit tests and in the end resulted in a nice reusable module.

## Documentation

Visit [Read the Docs](https://mqfactory.readthedocs.org) for the full documentation, including overviews and several examples.

===============================
Zero-Netcat
===============================


Netcat style utility using ZeroMQ sockets

* Free software: MIT license

Features
--------

* Simple command line ZeroMQ sockets for use in shell scripts and other CLI stuff


Installation
-----------

``python setup.py install``

Usage
-----

Usage ::

   zeronc [-h] [--io-threads IO_THREADS] [--ipv6] [--send-hwm SEND_HWM]
              [--receive-hwm RECEIVE_HWM] [--subscribe SUBSCRIBE]
              [--topic TOPIC] [--buffer-size BUFFER_SIZE] [--output OUTPUT]
              address [address ...]

* io-threads refers to the number of IO threads to allocate to ZeroMQ
* ipv6 enables ipv6 addressing in addition to ipv4
* send-hwm is the number of bytes to be queued before discarding or blocking outgoing messages
* receive-hwm is the number of bytes to be queued before discarding or blocking incoming messages
* subscribe (for SUB sockets) subscribes to a given topic - default is to subscribe to all messages, can be used multiple times
* topic (for PUB sockets) the topic to send messages on (default is ``default_topic``)
* buffer-size is the buffer size to use for incoming reads
* output specifies the file name to write output, default is standard out

address refers to a triple in the format <bind | connect> <socket type> <address>

multiple address of the same direction can be provided (reading or writing)

When multiple addresses are provided, incoming data will be fair queued between address (PUSH-PULL) and outgoing data will be broadcast
to all addresses (PUB-SUB)

For example: ``bind sub tcp://127.1:5001`` binds a SUB socket to port 5001

Available socket types are PUB / PUSH in writing mode, and SUB / PULL for read


TODO
----

This was a quick weekend project. Could use some more thorough testing and some friendliness with slow stdout consumers.


Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

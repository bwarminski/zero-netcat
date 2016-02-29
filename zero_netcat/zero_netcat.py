# -*- coding: utf-8 -*-

import six, sys, argparse, zmq, codecs, os
import random, time

# zeronc <bind|connect> <type> <address>

SOCKET_FROM_STR = {
    'pub' : zmq.PUB,
    'sub' : zmq.SUB,
    'push' : zmq.PUSH,
    'pull' : zmq.PULL
}

SENDS = ['pub', 'push']
RECEIVES = ['sub', 'pull']


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='Connects stdin and stdout to a ZeroMQ socket')
    parser.add_argument('--io-threads', type=int, default=1)
    parser.add_argument('--ipv6', action='store_true')
    parser.add_argument('--send-hwm', type=int, default=1000)
    parser.add_argument('--receive-hwm', type=int, default=1000)
    parser.add_argument('--subscribe', action='append')
    parser.add_argument('--topic', default='default_topic')
    parser.add_argument('bind_connect', choices=['bind', 'connect'])
    parser.add_argument('type', choices=SOCKET_FROM_STR.keys(), metavar='type')
    parser.add_argument('address')
    options = parser.parse_args(args)

    context = zmq.Context(options.io_threads)
    context.set(zmq.IPV6, 1 if options.ipv6 else 0)

    socket = context.socket(SOCKET_FROM_STR[options.type])
    send(socket, options) if options.type in SENDS else receive(socket, options)

def send(socket, options):
    socket.setsockopt(zmq.SNDHWM, options.send_hwm)
    is_pub = options.type == 'pub'
    if options.bind_connect == 'bind':
        socket.bind(options.address)
    else:
        socket.connect(options.address)

    input = os.fdopen(sys.stdin.fileno(), 'r', 1)
    while True:
        line = input.readline()
        if not line: break
        if is_pub:
            socket.send_multipart([options.topic.encode('utf-8'), line.rstrip().encode('utf-8')])
        else:
            socket.send_string(line)


def receive(socket, options):
    socket.setsockopt(zmq.RCVHWM, options.receive_hwm)
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    socket.bind(options.address) if options.bind_connect == 'bind' else socket.connect(options.address)
    if options.type == 'sub':
        if not options.subscribe:
            socket.set_string(zmq.SUBSCRIBE, six.u(''))
        else:
            for topic in options.subscribe:
                socket.set_string(zmq.SUBSCRIBE, six.u(topic))

    while True:
        if options.type == 'sub':
            socket.recv_string() #topic
        six._print(socket.recv_string())
    pass

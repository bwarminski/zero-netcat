# -*- coding: utf-8 -*-

import six, sys, argparse, zmq, codecs, os, zmq.devices
from six.moves import range

# zeronc <bind|connect> <type> <address>

SOCKET_FROM_STR = {
    'pub': zmq.PUB,
    'sub': zmq.SUB,
    'push': zmq.PUSH,
    'pull': zmq.PULL
}

SENDS = ['pub', 'push']
RECEIVES = ['sub', 'pull']


class AddressAction(argparse.Action):
    def __call__(self, parent_parser, namespace, values, option_string=None):
        if len(values) % 3 != 0:
            raise argparse.ArgumentError(self, "Address requires three arguments per address")
        parser = argparse.ArgumentParser()
        parser.add_argument('bind_connect', choices=['bind', 'connect'])
        parser.add_argument('type', choices=SOCKET_FROM_STR.keys(), metavar='type')
        parser.add_argument('address')
        setattr(namespace, self.dest, [parser.parse_args(values[i:i + 3]) for i in range(0, len(values), 3)])


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='Connects stdin and stdout to a ZeroMQ socket')
    parser.add_argument('--io-threads', type=int, default=1)
    parser.add_argument('--ipv6', action='store_true')
    parser.add_argument('--send-hwm', type=int, default=1000)
    parser.add_argument('--receive-hwm', type=int, default=1000)
    parser.add_argument('--subscribe', action='append')
    parser.add_argument('--topic', default=None)
    parser.add_argument('--buffer-size', type=int, default=100)
    parser.add_argument('address', nargs='+', action=AddressAction)
    options = parser.parse_args(args)
    context = zmq.Context.instance(options.io_threads)
    context.set(zmq.IPV6, 1 if options.ipv6 else 0)
    send(context, options) if options.address[0].type in SENDS else receive(context, options)


def send(context, options):
    if len(options.address) != 1:
        raise "Only one output address is supported"

    addr = options.address[0]
    socket = context.socket(SOCKET_FROM_STR[addr.type])
    socket.set(zmq.SNDHWM, options.send_hwm)
    if addr.bind_connect == 'bind':
        socket.bind(addr.address)
    else:
        socket.connect(addr.address)

    wrapped_input = codecs.getreader('utf-8')(os.fdopen(sys.stdin.fileno(), 'r', options.buffer_size))
    while True:
        line = wrapped_input.readline()
        if not line:
            break
        if options.topic is None:
            socket.send(line.rstrip().encode('utf-8'))
        else:
            socket.send_multipart([options.topic.encode('utf-8'), line.rstrip().encode('utf-8')])


def receive(context, options):
    poller = zmq.Poller()
    addrs = {}
    for addr in options.address:
        socket = context.socket(SOCKET_FROM_STR[addr.type])
        socket.set(zmq.RCVHWM, options.receive_hwm)

        if addr.type == 'sub':
            if not options.subscribe:
                socket.set_string(zmq.SUBSCRIBE, six.u('').encode('utf-8'))
            else:
                for topic in options.subscribe:
                    socket.set_string(zmq.SUBSCRIBE, six.u(topic).encode('utf-8'))

        if addr.bind_connect == 'bind':
            socket.bind(addr.address)
        else:
            socket.connect(addr.address)
        poller.register(socket, zmq.POLLIN)
        addrs[socket] = addr

    while True:
        events = dict(poller.poll())
        for socket in events.keys():
            if addrs[socket].type == 'sub':
                socket.recv(copy=False)  # topic
            six.print_(socket.recv_string().encode('utf-8'), flush=True)

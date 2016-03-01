# -*- coding: utf-8 -*-

import six, sys, argparse, zmq, codecs, os, zmq.devices, time
from six.moves import range

# zeronc <bind|connect> <type> <address>

SOCKET_FROM_STR = {
    'pub' : zmq.PUB,
    'sub' : zmq.SUB,
    'push' : zmq.PUSH,
    'pull' : zmq.PULL
}

SENDS = ['pub', 'push']
RECEIVES = ['sub', 'pull']

class AddressAction(argparse.Action):
    def __call__(self, parent_parser, namespace, values, option_string=None):
        if len(values) % 3 != 0: raise argparse.ArgumentError(self, "Address requires three arguments per address")
        parser = argparse.ArgumentParser()
        parser.add_argument('bind_connect', choices=['bind', 'connect'])
        parser.add_argument('type', choices=SOCKET_FROM_STR.keys(), metavar='type')
        parser.add_argument('address')
        setattr(namespace, self.dest, [parser.parse_args(values[i:i+3]) for i in range(0, len(values), 3)])

def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='Connects stdin and stdout to a ZeroMQ socket')
    parser.add_argument('--io-threads', type=int, default=1)
    parser.add_argument('--ipv6', action='store_true')
    parser.add_argument('--send-hwm', type=int, default=1000)
    parser.add_argument('--receive-hwm', type=int, default=1000)
    parser.add_argument('--subscribe', action='append')
    parser.add_argument('--topic', default='default_topic')
    parser.add_argument('--buffer-size', type=int, default=100)
    parser.add_argument('--output', default='')
    parser.add_argument('address', nargs='+', action=AddressAction)
    options = parser.parse_args(args)
    context = zmq.Context.instance(options.io_threads)
    context.set(zmq.IPV6, 1 if options.ipv6 else 0)
    send(context, options) if options.address[0].type in SENDS else receive(context, options)


def send(context, options):
    bcast = context.socket(zmq.PUB)
    bcast.bind('inproc://bcast')

    for addr in options.address:
        proxy = zmq.devices.ThreadProxy(zmq.SUB, SOCKET_FROM_STR[addr.type])
        proxy.setsockopt_out(zmq.SNDHWM, options.send_hwm)
        if addr.bind_connect == 'bind':
            proxy.bind_out(addr.address)
        else:
            proxy.connect_out(addr.address)
        proxy.setsockopt_in(zmq.SUBSCRIBE, six.u('').encode('utf-8'))
        proxy.connect_in('inproc://bcast')
        proxy.start()

    input = codecs.getreader('utf-8')(os.fdopen(sys.stdin.fileno(), 'r', options.buffer_size))
    while True:
        line = input.readline()
        if not line: break
        bcast.send_multipart([options.topic.encode('utf-8'), line.rstrip().encode('utf-8')])


def receive(context, options):
    input = context.socket(zmq.PULL)
    input.bind('inproc://input')
    output = sys.stdout.fileno()
    fdout = len(options.output) > 0
    if fdout:
        output = os.open(options.output, os.O_WRONLY)

    for addr in options.address:
        proxy = zmq.devices.ThreadProxy(SOCKET_FROM_STR[addr.type], zmq.PUSH)
        proxy.setsockopt_in(zmq.RCVHWM, options.receive_hwm)
        if addr.type == 'sub':
            if not options.subscribe:
                proxy.setsockopt_in(zmq.SUBSCRIBE, six.u('').encode('utf-8'))
            else:
                for topic in options.subscribe:
                    proxy.setsockopt_in(zmq.subscribe, six.u(topic).encode('utf-8'))

        if addr.bind_connect == 'bind':
            proxy.bind_in(addr.address)
        else:
            proxy.connect_in(addr.address)
        proxy.connect_out('inproc://input')
        proxy.start()

    if fdout:
        while True:
            input.recv_string() #topic
            os.write(output, input.recv_string().encode('utf-8'))
            os.write(output, '\n'.encode('utf-8'))
    else:
        while True:
            input.recv_string() #topic
            six.print_(input.recv_string(), flush=True)




# -*- coding: utf-8 -*-

import six, sys, argparse, zmq, codecs, os, zmq.devices, time
from six.moves import range
import select
import ctypes
from ctypes import *

# zeronc <bind|connect> <type> <address>

SOCKET_FROM_STR = {
    'pub' : zmq.PUB,
    'sub' : zmq.SUB,
    'push' : zmq.PUSH,
    'pull' : zmq.PULL
}

SENDS = ['pub', 'push']
RECEIVES = ['sub', 'pull']

LIBC = CDLL(None)

# Shit just got real


# File API.
#
# A FILE_ptr type is used instead of c_void_p because technically a pointer
# to structure can have a different size or alignment to a void pointer.
#
# Note that the file api may change.
#

class FILE(ctypes.Structure):
    pass
FILE_ptr = ctypes.POINTER(FILE)

PyFile_FromFile = ctypes.pythonapi.PyFile_FromFile
PyFile_FromFile.restype = ctypes.py_object
PyFile_FromFile.argtypes = [FILE_ptr,
                            ctypes.c_char_p,
                            ctypes.c_char_p,
                            ctypes.CFUNCTYPE(ctypes.c_int, FILE_ptr)]

PyFile_AsFile = ctypes.pythonapi.PyFile_AsFile
PyFile_AsFile.restype = FILE_ptr
PyFile_AsFile.argtypes = [ctypes.py_object]

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

    input = codecs.getreader('utf-8')(os.fdopen(sys.stdin.fileno(), 'r', options.buffer_size))
    while True:
        line = input.readline()
        if not line: break
        if options.topic == None:
            socket.send(line.rstrip().encode('utf-8'))
        else:
            socket.send_multipart([options.topic.encode('utf-8'), line.rstrip().encode('utf-8')])


def receive(context, options):
    input = context.socket(zmq.PULL)
    input.bind('inproc://input')

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

    poller = select.poll()
    poller.register(sys.stdout, select.POLLOUT)
    while True:
        poller.poll()
        input.recv_string() #topic
        buf = input.recv_string().encode('utf-8')

        six.print_(input.recv_string().encode('utf-8'), flush=True)




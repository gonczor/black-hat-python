#!/usr/bin/env python

import sys
import socket
import threading

from scipy.constants.constants import lb


def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # noinspection PyBroadException
    try:
        server.bind((local_host, local_port))
    except:
        print 'Failed on {}:{}! Search for another port or privileges.'.format(local_host, local_port)
        sys.exit(0)
    else:
        server.listen(5)
        while True:
            client, address = server.accept()
            print '==> Incoming connection from {}:{}'.format(client, address)
            proxy_thread = threading.Thread(target=proxy_handler, args=(client,
                                                                        remote_host,
                                                                        remote_port,
                                                                        receive_first))
            proxy_thread.start()


def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))
    if receive_first:
        remote_buffer = receive_from(remote_socket)
        hex_dump(remote_buffer)
        remote_buffer = request_handler(remote_buffer)

        if len(remote_buffer):
            print '==> Received data from {}:{}'.format(remote_host, remote_port)
            print '<== Sending {} bytes to {}'.format(len(remote_buffer), client_socket)
            client_socket.send(remote_buffer)
    while True:
        local_buffer = receive_from(client_socket)

        if len(local_buffer):
            print '==> Received {} bytes from {}.'.format(len(local_buffer), client_socket)
            hex_dump(local_buffer)
            local_buffer = request_handler(local_buffer)
            remote_socket.send(local_buffer)
            print '<== Sent {} bytes to {}.'.format(len(local_buffer), remote_socket)
            remote_buffer = receive_from(remote_socket)
            if len(remote_buffer):
                print '==> Received {} bytes from {}.'.format(len(local_buffer), remote_socket)
                hex_dump(remote_buffer)
                remote_buffer = request_handler(remote_buffer)
                client_socket.send(remote_buffer)
                print '<== Sent {} bytes to {}'.format(len(remote_buffer), client_socket)
            if not len(remote_buffer) and not len(local_buffer):
                client_socket.close()
                remote_socket.close()
                print '[*] No more data. Shutting down.'
                break


def receive_from(connection):
    buf = ''
    connection.settimeout(1)
    # noinspection PyBroadException
    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            else:
                buf += data
    except:
        pass
    return buf


def hex_dump(source, length=16):
    result = []
    digits = 4 if isinstance(source, unicode) else 2
    for i in xrange(0, len(source), length):
        s = source[i:i+length]
        hexa = b''.join(['%0*X' % (digits, ord(x) for x in s)])
        text = b''.join([x if 0x20 <= ord(x) < 0x7F else b'.' for x in s])
        result.append(b'%04X %-*s' % (i, length*(digits + 1), hexa, text))

    print b'\n'.join(result)


def request_handler(buf):
    return buf


def response_handler(buf):
    return buf


def main():
    if len(sys.argv[1:]) != 5:
        print 'Usage: python tcp_proxy.py [local_host] [local_port] [remote_host] [remote_port] [receive_first]\n' \
              '[receive_first] should be True or False'
        sys.exit(0)

    local_host = sys.argv[1]
    local_port = sys.argv[2]

    remote_host = sys.argv[3]
    remote_port = sys.argv[4]

    if 'True' in sys.argv[5]:
        receive_first = True
    else:
        receive_first = False

    server_loop(local_host=local_host,
                local_port=local_port,
                remote_host=remote_host,
                remote_port=remote_port,
                receive_first=receive_first)

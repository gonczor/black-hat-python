#!/usr/bin/env python

import sys
import socket
import getopt
import threading
import subprocess

listen = False
command = False
upload = False
execute = ''
target = ''
upload_destination = ''
port = ''

usage = 'usage: python my_nc.py -t target_host -p target port\n' \
        'Optional arguments are:\n' \
        '-l --listen listen on [host]:[port]\n' \
        '-e --execute=file_to_run execute [file_to_run]\n' \
        '-c --command initialize command line\n' \
        '-u --upload=destination when receives connection sends file and saves to [destination]\n'


def main():
    global usage
    global listen
    global command
    global upload
    global execute
    global target
    global upload_destination
    global port

    if not len(sys.argv[1:]):
        print usage
        sys.exit(0)

    # get cli options
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'le:t:p:cu',
                                   ['listen', 'execute', 'target', 'port', 'command', 'upload'])
    except getopt.GetoptError as error:
        print str(error)
        print usage
        sys.exit(-1)

    parse_opts(opts)
    if not listen and len(target) and port > 0:
        # enter ctrl-d to terminate sending to stdin
        buf = sys.stdin.read()
        client_sender(buf)

    if listen:
        server_loop()


def client_sender(buf):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((target, port))
        if len(buf):
            client.send(buf)
        while True:
            data_len = 1
            response = ''

            while data_len:

                data = client.recv(4096)
                data_len = len(data)
                response += data
                if data_len < 4096:
                    break

            print response

            buf = raw_input()
            buf += '\n'

            client.send(buf)

    except Exception:
        print 'Unknown error'
        client.close()


def server_loop():
    global target

    if not len(target):
        target = '0.0.0.0'

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    while True:
        client_socket, address = server.accept()
        client_thread = threading.Thread(target=client_handler,
                                         args=(client_socket,))
        client_thread.start()


def run_command(c):
    c = c.rstrip()

    try:
        output = subprocess.check_output(c, stderr=subprocess.STDOUT, shell=True)
    except:
        output = 'Could not execute command'

    return output


def client_handler(client_socket):
    global upload
    global execute
    global command

    if len(upload_destination):
        file_buffer = ''
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            else:
                file_buffer += data

        try:
            fd = open(upload_destination, 'wb')
            fd.write(file_buffer)
            fd.close()

            client_socket.send('Saved in {}'.format(upload_destination))
        except:
            client_socket.send('Couldn\'t save')

    if len(execute):
        output = run_command(execute)
        client_socket.send(output)

    if command:

        while True:
            client_socket.send('>')
            cmd_buffer = ''
            while '\n' not in cmd_buffer:
                cmd_buffer += client_socket.recv(4096)

            response = run_command(cmd_buffer)
            client_socket.send(response)


def parse_opts(opts):
    global usage
    global listen
    global command
    global upload
    global execute
    global target
    global upload_destination
    global port

    for option, argument in opts:
        if option in ('-l', '--listen'):
            listen = True
        elif option in ('-e', '--execute'):
            execute = argument
        elif option in ('-c', '--command'):
            command = True
        elif option in ('-u', '--upload'):
            upload_destination = argument
        elif option in ('-t', '--target'):
            target = argument
        elif option in ('-p', '--port'):
            port = int(argument)
        else:
            print 'Unsupported option'
            sys.exit(-1)


if __name__ == '__main__':
    main()

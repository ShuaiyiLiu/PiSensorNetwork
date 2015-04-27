#! /usr/bin/env python
'''
This module defines functions that upload data and errors from nodes to server.
'''
import socket
import json
import datetime
import sys

def _connectServer():
    with open("config/node.json") as nodeConfigFile:
        serverConfig = json.load(nodeConfigFile)['server']
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # TODO: supporting argument selecting host and port
    host = serverConfig['host']
    port = serverConfig['port']
    sock.connect((host, port))
    curTime = str(datetime.datetime.now())[0:-7]
    print curTime + '   Node has connected to server\n'
    sys.stdout.flush()
    return sock

def upload(data):
    try:
        sock = _connectServer()
        sock.sendall(data)
    except socket.error:
        print 'cannot send data to server.'
        pass

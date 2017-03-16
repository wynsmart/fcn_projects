from __future__ import print_function
import socket


class MyTCP:
    def __init__(self):
        self.sock = None

    def connect(self, netloc):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(netloc)

    def sendall(self, data):
        self.sock.sendall(data)

    def recv(self):
        BUFFER_SIZE = 256
        return self.sock.recv(BUFFER_SIZE)

    def close(self):
        self.sock.close()

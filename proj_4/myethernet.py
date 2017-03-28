from __future__ import print_function
from struct import pack, unpack
import socket

from utils import IFNAME, hexprint

IP_FRAME = '\x08\x00'


class MyEthernet:
    '''Customized Ethernet on datalink layer
    '''
    def __init__(self, dst_mac):
        self.send_sock = socket.socket(
            socket.PF_PACKET,
            socket.SOCK_RAW,
            socket.htons(3), )
        self.recv_sock = socket.socket(
            socket.PF_PACKET,
            socket.SOCK_RAW,
            socket.htons(3), )

        self.send_sock.bind((IFNAME, 0))
        self.recv_sock.setblocking(0)

        self.src_mac = self.send_sock.getsockname()[-1]
        self.dst_mac = dst_mac

    def send(self, data, frame_type=IP_FRAME):
        '''send specific frame typed data
        '''
        eth_packet = self._build_packet(data, frame_type)
        bytes_sent = 0
        while bytes_sent < len(eth_packet):
            bytes_sent += self.send_sock.send(eth_packet[bytes_sent:])

    def recv(self, bufsize, frame_type=IP_FRAME):
        '''receive data from ethernet, filtered by given frame type
        '''
        try:
            recv_packet = self.recv_sock.recv(bufsize)
            return self._filter_packets(recv_packet, frame_type)
        except:
            return None

    def _build_packet(self, body, frame_type):
        '''Assemble ethernet header fields appending body
        [REFERENCE] https://en.wikipedia.org/wiki/Ethernet_frame
        '''
        # Ethernet Header
        eth_hdr = pack('!6s6s2s', self.dst_mac, self.src_mac, frame_type)
        return eth_hdr + body

    def _filter_packets(self, recv_packet, frame_type):
        '''verify the following attributes of received packet
        (src_mac, frame_type)
        returns the packet body if the verification is passed,
        else return None
        '''
        dst_mac = recv_packet[0:6]
        if dst_mac != self.src_mac:
            return None

        packet_type = recv_packet[12:14]
        if packet_type != frame_type:
            return None

        return recv_packet[14:]

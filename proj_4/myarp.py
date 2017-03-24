from __future__ import print_function
import socket
import struct
import sys
import binascii
from uuid import getnode

class MyARP:

    def __init__(self):
        self.src_ip = self._get_src_ip()
        self.src_hwaddr = getnode()
        # Call API to get DST IP
        self.dst_hwaddr = None
        self.send_sock = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))
        self.send_sock.bind(('eth0', 0))
        self.recv_sock = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))

    def arp_request(self, ip_addr):
        self._send(ip_addr)
        mac_addr = self._recv(ip_addr)
        return mac_addr

    def _build_packet(self, ip_addr):
        dst_ip = socket.inet_aton(ip_addr)
        # Ethernet Header
        # "!6s6s2s"
        ether_type = '\x08\x06'
        dst_mac =  '\xFF' * 6
        src_mac = '{:012x}'.format(self.src_hwaddr)
        src_mac = ''.join([struct.pack('!B', int(src_mac[i: i+2], base=16)) for i in range(0, 12, 2)])
        print('dst:', list(dst_mac))
        print('src:', list(src_mac))
        # ARP Header
        # "!2s2s1s1s2s"
        hware_type = '\x00\x01'
        proto_type = '\x08\x00'
        hware_size = '\x06'
        proto_size = '\x04'
        opcode = '\x00\x01'
        src_ip = socket.inet_aton(self.src_ip)

        # ARP Data
        # "!6s4s"
        arp_dst_mac = '\x00'*6

        # Create Packet
        eth_hdr = struct.pack('!6s6s2s', dst_mac, src_mac, ether_type)
        print(list(eth_hdr))
        arp_hdr = struct.pack('!2s2s1s1s2s', hware_type, proto_type, hware_size, proto_size, opcode)
        arp_data = struct.pack('!6s4s', src_mac, src_ip) + struct.pack('!6s4s', arp_dst_mac, dst_ip)

        arp_packet = eth_hdr + arp_hdr + arp_data
        # exit(list(arp_packet))
        return arp_packet

    def _get_src_ip(self):
        # TODO: find out local ip
        return '172.16.248.10'

    def _send(self, ip_addr):
        self.send_sock.send(self._build_packet(ip_addr))

    def _recv(self, ip_addr):
        arp_response = self.recv_sock.recv(4096)
        sender_ip = struct.unpack('!4B', arp_response[0x26:0x2a])
        local_ip = tuple([int(i) for i in self.src_ip.split('.')])
        print('zzz', sender_ip, local_ip)
        if sender_ip == local_ip:
            self.dst_hwaddr = arp_response[0x16:0x1c]
            print('jjj', self.send_sock.getsockname())
        return self.dst_hwaddr


if __name__ == "__main__":
    arp = MyARP()
    host = 'david.choffnes.com'
    ip_addr = socket.gethostbyname(host)
    print(ip_addr)
    mac_addr = arp.arp_request(ip_addr)
    print('mac:', list(mac_addr))

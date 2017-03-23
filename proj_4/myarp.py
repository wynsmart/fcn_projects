import socket
import struct
import sys
import binascii
from uuid import getnode

class MyARP:

    def __init__(self):
        self.src_ip = socket.inet_aton(self._get_src_ip())
        self.src_hwaddr = self.format_mac(getnode()).replace(':','')
        # Call API to get DST IP
        self.dst_ip = socket.inet_aton(None)
        self.dst_hwaddr = None
        self.send_sock = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))
        self.recv_sock = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))

    def _build_packet(self):
        # Ethernet Header
        # "!6s6s2s"
        ether_type = '\x08\x06'
        dst_broadcast_hwaddr =  '\xff\xff\xff\xff\xff\xff'
        src_mac = self.src_hwaddr.decode('hex')

        # ARP Header
        # "!2s2s1s1s2s"
        hware_type = '\x00\x01'
        proto_type = '\x08\x00'
        hware_size = '\x06'
        proto_size = '\x04'
        opcode = '\x00\x01'

        # ARP Data
        # "!6s4s"
        dst_mac = '\x00\x00\x00\x00\x00\x00'

        # Create Packet
        eth_hdr = struct.pack('!6s6s2s', ether_type, dst_broadcast_hwaddr, src_mac)
        arp_hdr = struct.pack('!2s2s1s1s2s', hware_type, proto_type, hware_size, proto_size, opcode)
        arp_data = struct.pack('!6s4s', src_mac, self.src_ip) + struct.pack('!6s4s', dst_mac, self.dst_ip)

        arp_packet = eth_hdr + arp_hdr + arp_data
        return arp_packet

    def format_mac(self, mac_int):
        mac_hex = iter(hex(address)[2:].zfill(12))
        mac_hex = ":".join(i + next(h) for i in h)
        return mac_hex

    def _get_src_ip(self):
        # TODO: find out local ip
        return '172.16.248.10'

    def _send(self):
        send_sock.send(_build_packet())

    def _recv(self):
        arp_response = recv_sock.recvfrom(2048)
        if arp_response[0][28:32] == self.dst_ip:
            self.dst_hwaddr = binascii.hexlify(arp_response[0][6:12]).swapcase()

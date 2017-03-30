from __future__ import print_function
from struct import pack, unpack
import socket

from utils import IFNAME, hexprint, Timer
from myethernet import MyEthernet

ARP_FRAME = '\x08\x06'


class MyARP:
    def __init__(self, src_ip):
        dst_mac = '\xFF' * 6
        self.ethernet = MyEthernet(dst_mac)
        self.src_ip = src_ip

    def lookup(self, ip_addr, retry=3):
        '''Look up the MAC address of given IP address
        '''
        if not retry:
            exit('ARP failed, please retry later')
        arp_packet = self._build_packet(ip_addr)
        self.ethernet.send(arp_packet, frame_type=ARP_FRAME)
        timer = Timer(10)
        mac_addr = None
        while mac_addr is None and not timer.timeout():
            data = self.ethernet.recv(4096, frame_type=ARP_FRAME)
            mac_addr = self._filter_packets(data)

        if mac_addr is None:
            return self.lookup(ip_addr, retry=retry - 1)

        return mac_addr

    def _build_packet(self, ip_addr):
        # ARP Header
        # "!2s2s1s1s2s"
        hware_type = '\x00\x01'
        proto_type = '\x08\x00'
        hware_size = '\x06'
        proto_size = '\x04'
        opcode = '\x00\x01'
        src_ip = socket.inet_aton(self.src_ip)
        dst_ip = socket.inet_aton(ip_addr)
        arp_dst_mac = '\x00' * 6

        # Create Packet
        arp_hdr = pack(
            '!2s2s1s1s2s',
            hware_type,
            proto_type,
            hware_size,
            proto_size,
            opcode, )
        arp_data = pack(
            '!6s4s6s4s',
            self.ethernet.src_mac,
            src_ip,
            arp_dst_mac,
            dst_ip, )

        return arp_hdr + arp_data

    def _filter_packets(self, recv_packet):
        '''verify the following attributes of received packet
        (receiver_ip)
        returns the packet body if the verification is passed,
        else return None
        '''
        if recv_packet is None:
            return None
        receiver_ip = recv_packet[24:28]
        local_ip = socket.inet_aton(self.src_ip)
        if receiver_ip != local_ip:
            return None
        return recv_packet[8:14]

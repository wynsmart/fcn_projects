from __future__ import print_function
from struct import pack, unpack
import socket
import fcntl
import random

from utils import calc_checksum, IFNAME, log, hexprint
from myethernet import MyEthernet
from myarp import MyARP


class MyIP:
    '''Customized IP on network layer
    '''

    def __init__(self, dst_ip):
        self.ethernet = None

        self.src_ip = self._get_src_ip()
        self.dst_ip = dst_ip
        self.arp = MyARP(self.src_ip)

    def send(self, data):
        if self.ethernet == None:
            log('ARP looking up for', self.dst_ip)
            dst_mac = self.arp.lookup(self.dst_ip)
            log('MAC found:', dst_mac)
            self.ethernet = MyEthernet(dst_mac)

        ip_packet = self._build_packet(data)
        self.ethernet.send(ip_packet)

    def recv(self, bufsize=4096):
        data = None
        while data is None:
            recv_packet = self.ethernet.recv(bufsize)
            data = self._filter_packets(recv_packet)
        hexprint(recv_packet)
        return data

    def _build_packet(self, body):
        '''Assemble IP header fields appending body
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |Version|  IHL  |Type of Service|          Total Length         |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |         Identification        |Flags|      Fragment Offset    |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |  Time to Live |    Protocol   |         Header Checksum       |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                       Source Address                          |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                    Destination Address                        |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                    Options                    |    Padding    |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        [REFERENCE] https://en.wikipedia.org/wiki/IPv4
        '''
        version = 4
        ihl = 5
        dscp = 0
        ecn = 0
        total_length = ihl * 4 + len(body)
        packet_id = random.randint(1, 65535)
        flags = 0
        frag_offset = 0
        ttl = 255
        protocol = socket.IPPROTO_TCP
        h_checksum = 0
        src_ip = socket.inet_aton(self.src_ip)
        dst_ip = socket.inet_aton(self.dst_ip)

        header = pack(
            '!BBH HH BBH 4s 4s',
            (version << 4) | ihl,
            (dscp << 2) | ecn,
            total_length,
            packet_id,
            (flags << 13) | frag_offset,
            ttl,
            protocol,
            h_checksum,
            src_ip,
            dst_ip, )

        h_checksum = self._calc_checksum(header)
        header = header[:10] + pack('!H', h_checksum) + header[12:]
        return header + body

    def _get_src_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        src_ip = socket.inet_ntoa(
            fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                pack('256s', IFNAME[:15]))[20:24])
        return src_ip

    def _calc_checksum(self, header):
        msg = header[:10] + pack('!H', 0) + header[12:]
        return calc_checksum(msg)

    def _filter_packets(self, ip_packet):
        '''verify the following attributes of received packet
        protocol, dst_ip, src_ip, ip_checksum,
        returns the packet body if the verification is passed,
        else return None
        '''
        if ip_packet is None:
            return None
        # Network Layer
        # log('filtering Network Layer')
        ip_h_lengh = (unpack('!B', ip_packet[0])[0] & 0x0F) * 4
        ip_p_lengh = unpack('!H', ip_packet[2:4])[0]
        ip_header = ip_packet[:ip_h_lengh]
        protocol = unpack('!B', ip_header[9])[0]
        src_ip = socket.inet_ntoa(ip_header[12:16])
        dst_ip = socket.inet_ntoa(ip_header[16:20])
        ip_checksum = unpack('!H', ip_header[10:12])[0]

        if (protocol, src_ip, dst_ip, ip_checksum) != (
                socket.IPPROTO_TCP,
                self.dst_ip,
                self.src_ip,
                self._calc_checksum(ip_header), ):
            return None

        return ip_packet[ip_h_lengh:ip_p_lengh]

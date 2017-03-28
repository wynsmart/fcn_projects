from __future__ import print_function
from struct import pack, unpack
import subprocess
import socket
import fcntl
import random
import re

from utils import calc_checksum, IFNAME, log, hexrepr
from myethernet import MyEthernet
from myarp import MyARP


class MyIP:
    '''Customized IP on network layer
    '''

    def __init__(self, dst_ip):
        self.src_ip = self._get_src_ip()
        self.dst_ip = dst_ip

        # ARP looking up for gateway
        self.arp = MyARP(self.src_ip)
        gateway_ip = self._get_gateway_ip()
        log('ARP looking up for', gateway_ip)
        dst_mac = self.arp.lookup(gateway_ip)
        log('MAC found:', hexrepr(dst_mac))
        self.ethernet = MyEthernet(dst_mac)

    def send(self, data):
        '''send TCP packet over IP
        '''
        ip_packet = self._build_packet(data)
        self.ethernet.send(ip_packet)

    def recv(self, bufsize=4096):
        '''receive IP packet, and receive the data body (AKA TCP packet)
        '''
        data = None
        while data is None:
            recv_packet = self.ethernet.recv(bufsize)
            data = self._filter_packets(recv_packet)
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
        '''use `ifconfig` to get local ip address
        '''
        if_info = subprocess.check_output(['ifconfig'])
        pattern = r"^{}.+\n\s+inet addr:(\S+).+$".format(IFNAME)
        src_ip = re.search(pattern, if_info, re.M).group(1)
        return src_ip

    def _get_gateway_ip(self):
        '''use `route -n` to get gateway ip address
        '''
        route_info = subprocess.check_output(['route', '-n'])
        pattern = r"^0\.0\.0\.0\s+(\S+).+G.+{}$".format(IFNAME)
        gateway_ip = re.search(pattern, route_info, re.M).group(1)
        return gateway_ip

    def _calc_checksum(self, header):
        '''calculate checksum for ip headers
        '''
        msg = header[:10] + pack('!H', 0) + header[12:]
        return calc_checksum(msg)

    def _filter_packets(self, ip_packet):
        '''verify the following attributes of received packet
        (protocol, dst_ip, src_ip, ip_checksum)
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

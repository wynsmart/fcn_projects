from __future__ import print_function
from struct import pack, unpack
import socket

from utils import calc_checksum


class MyIP:
    '''Customized IP on network layer
    '''

    def __init__(self):
        self.src_ip = self._get_src_ip()
        self.dst_ip = None

        self.send_sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_RAW,
            socket.IPPROTO_RAW, )
        self.recv_sock = socket.socket(
            socket.PF_PACKET,
            socket.SOCK_RAW,
            socket.htons(3), )
        # self.recv_sock = socket.socket(
        #     socket.AF_INET,
        #     socket.SOCK_RAW,
        #     socket.IPPROTO_TCP, )

    def connect(self, dst_host):
        self.dst_ip = socket.gethostbyname(dst_host)

    def sendto(self, data, dst_port):
        ip_packet = self._build_packet(data)
        bytes_sent = 0
        while bytes_sent < len(ip_packet):
            bytes_sent += self.send_sock.sendto(ip_packet[bytes_sent:],
                                                (self.dst_ip, dst_port))

    def recv(self, bufsize):
        data = None
        while data is None:
            recv_packet, addr = self.recv_sock.recvfrom(bufsize)
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
        total_length = 0
        packet_id = 54321
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

        packet = header + body
        return packet

    def _get_src_ip(self):
        return '172.16.248.10'

    def _calc_checksum(self, header):
        msg = header[:10] + pack('!H', 0) + header[12:]
        return calc_checksum(msg)

    def _filter_packets(self, recv_packet):
        '''verify the following attributes of received packet
        protocol, dst_ip, src_ip, ip_checksum,
        returns the packet body if the verification is passed,
        else return None
        '''
        # Data Link Layer
        # log('filtering Data Link Layer')
        frame_type = unpack('!H', recv_packet[12:14])[0]
        if frame_type != 0x0800:
            # 0x0800 is the type of IP protocol
            return None

        # Network Layer
        # log('filtering Network Layer')
        ip_packet = recv_packet[14:]
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

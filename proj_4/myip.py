from __future__ import print_function
from struct import pack, unpack
import socket

from utils import calc_checksum


class MyIP:
    '''Customized IP on network layer
    '''

    def build_packet(self, src, dst, body):
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
        src_ip = socket.inet_aton(src)
        dst_ip = socket.inet_aton(dst)

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

    def _calc_checksum(self, header):
        msg = header[:10] + pack('!H', 0) + header[12:]
        return calc_checksum(msg)

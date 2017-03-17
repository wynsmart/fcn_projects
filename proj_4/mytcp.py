from __future__ import print_function
from struct import pack, unpack
import socket
import random

from myip import MyIP


class MyTCP:
    '''Customized TCP on transport layer
    '''
    # define TCP flags
    FIN, SYN, RST, PSH, ACK, URG, ECE, CWR = [1 << i for i in range(8)]

    def __init__(self):
        self.ip = MyIP()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                  socket.IPPROTO_RAW)
        self.src_host = self._get_self_ip()
        self.src_port = self._nextAvailablePort()
        self.dst_host = None
        self.dst_port = None
        self.seq_num = random.randrange(1 << 32)
        self.ack_num = 0

    def connect(self, netloc):
        dst_host, self.dst_port = netloc
        self.dst_host = socket.gethostbyname(dst_host)
        self._send(MyTCP.SYN, '')

    def sendall(self, data):
        self.sock.sendall(data)

    def recv(self, buff_size):
        return self.sock.recv(buff_size)

    def close(self):
        self.sock.close()

    def _send(self, flags, data):
        tcp_packet = self._build_packet(flags, data)
        ip_packet = self.ip.build_packet(self.src_host, self.dst_host,
                                         tcp_packet)
        self.sock.sendto(ip_packet, (self.dst_host, self.dst_port))

    def _build_packet(self, flags, body):
        '''Assemble TCP header fields appending body, reference at
        https://en.wikipedia.org/wiki/Transmission_Control_Protocol
        '''
        data_offset = 5
        ns = 0
        tcp_window = 1000
        checksum = 0
        urg_ptr = 0

        header = pack(
            '!HH L L BBH HH',
            self.src_port,
            self.dst_port,
            self.seq_num,
            self.ack_num,
            (data_offset << 4) | ns,
            flags,
            tcp_window,
            checksum,
            urg_ptr, )

        packet = header + body

        # patch calculated checksum into TCP packet
        checksum = self._calc_checksum(packet)
        packet = packet[:16] + pack('!H', checksum) + packet[18:]

        return packet

    def _calc_checksum(self, packet):
        '''Calculate parity checksum for TCP header and body
        Checksum:  16 bits

        The checksum field is the 16 bit one's complement of the one's
        complement sum of all 16 bit words in the header and text.  If a
        segment contains an odd number of header and text octets to be
        checksummed, the last octet is padded on the right with zeros to
        form a 16 bit word for checksum purposes.  The pad is not
        transmitted as part of the segment.  While computing the checksum,
        the checksum field itself is replaced with zeros.

        The checksum also covers a 96 bit pseudo header conceptually
        prefixed to the TCP header.  This pseudo header contains the Source
        Address, the Destination Address, the Protocol, and TCP length.
        This gives the TCP protection against misrouted segments.  This
        information is carried in the Internet Protocol and is transferred
        across the TCP/Network interface in the arguments or results of
        calls by the TCP on the IP.

                         +--------+--------+--------+--------+
                         |           Source Address          |
                         +--------+--------+--------+--------+
                         |         Destination Address       |
                         +--------+--------+--------+--------+
                         |  zero  |  PTCL  |    TCP Length   |
                         +--------+--------+--------+--------+

          The TCP Length is the TCP header length plus the data length in
          octets (this is not an explicitly transmitted quantity, but is
          computed), and it does not count the 12 octets of the pseudo
          header.
        '''
        pseudo_header = pack(
            '!4s 4s BBH',
            socket.inet_aton(self.src_host),
            socket.inet_aton(self.dst_host),
            0,
            socket.IPPROTO_TCP,
            len(packet), )

        if len(packet) % 2 != 0:
            packet += pack('!B', 0)

        msg = pseudo_header + packet

        checksum = 0
        for i in range(1, len(msg), 2):
            checksum += unpack('!H', msg[i - 1:i + 1])[0]
            checksum = (checksum >> 16) + (checksum & 0xFFFF)

        checksum = ~checksum & 0xFFFF
        return checksum

    def _get_self_ip(self):
        return '172.16.248.10'

    def _nextAvailablePort(self):
        return 50249


if __name__ == '__main__':
    mytcp = MyTCP()
    mytcp.connect(('david.choffnes.com', 80))
    # mytcp._send('hello world')

from __future__ import print_function
from struct import pack, unpack
import socket
import random
import time

from myip import MyIP
from utils import calc_checksum


class MyTCP:
    '''Customized TCP on transport layer
    '''
    # define TCP flags
    FIN, SYN, RST, PSH, ACK, URG, ECE, CWR = [1 << i for i in xrange(8)]

    def __init__(self):
        self.ip = MyIP()

        self.src_host = self._get_self_ip()
        self.src_port = self._nextAvailablePort()
        self.dst_host = None
        self.dst_port = None

        self.send_sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_RAW,
            socket.IPPROTO_RAW, )
        self.recv_sock = socket.socket(
            socket.PF_PACKET,
            socket.SOCK_RAW,
            socket.htons(3), )

        self.seq_num = random.randrange(1 << 32)
        self.ack_num = 0
        self.last_sent_size = 0

    def connect(self, netloc):
        dst_host, self.dst_port = netloc
        self.dst_host = socket.gethostbyname(dst_host)
        self.send_sock.connect((self.dst_host, self.dst_port))
        # TCP handshake
        self._send(MyTCP.SYN, '')
        self._recv(MyTCP.SYN | MyTCP.ACK, 256)
        self._send(MyTCP.ACK, '')

    def sendall(self, data):
        self._send(MyTCP.PSH, data)

    def _recv(self, flags, buff_size):
        data = None
        while data is None:
            recv_packet = self.recv_sock.recv(buff_size)
            data = self._verify_packet_and_get_data(recv_packet, flags)

        return data

    def close(self):
        self.send_sock.close()

    def _send(self, flags, data):
        tcp_packet = self._build_packet(flags, data)
        ip_packet = self.ip.build_packet(self.src_host, self.dst_host,
                                         tcp_packet)
        self.send_sock.sendall(ip_packet)
        if flags & MyTCP.ACK:
            self.last_sent_size = 0
        else:
            self.last_sent_size = len(data) or 1

    def _build_packet(self, flags, body):
        '''Assemble TCP header fields appending body
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |          Source Port          |       Destination Port        |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                        Sequence Number                        |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                    Acknowledgment Number                      |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |  Data |           |U|A|P|R|S|F|                               |
        | Offset| Reserved  |R|C|S|S|Y|I|            Window             |
        |       |           |G|K|H|T|N|N|                               |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |           Checksum            |         Urgent Pointer        |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                    Options                    |    Padding    |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                             data                              |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        [REFERENCE] https://en.wikipedia.org/wiki/Transmission_Control_Protocol
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
        checksum = self._calc_checksum(packet, self.src_host, self.dst_host)
        packet = packet[:16] + pack('!H', checksum) + packet[18:]

        return packet

    def _calc_checksum(self, packet, src_host, dst_host):
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
            socket.inet_aton(src_host),
            socket.inet_aton(dst_host),
            0,
            socket.IPPROTO_TCP,
            len(packet), )

        msg = pseudo_header + packet[:16] + pack('!H', 0) + packet[18:]
        return calc_checksum(msg)

    def _get_self_ip(self):
        return '172.16.248.10'

    def _nextAvailablePort(self):
        return 50249

    def _verify_packet_and_get_data(self, recv_packet, flags):
        '''verify the following attributes of received packet
        dst_ip, dst_port, src_ip, src_port, protocol, ip_checksum, tcp_checksum
        returns the parsed packet if the verification is passed,
        else return None
        '''
        # Data Link Layer
        frame_type = unpack('!H', recv_packet[12:14])[0]
        if frame_type != 0x0800:
            # 0x0800 is the type of IP protocol
            return None

        # Network Layer
        ip_packet = recv_packet[14:]
        ip_h_lengh = (unpack('!B', ip_packet[0])[0] & 0x0F) * 4
        ip_p_lengh = unpack('!H', ip_packet[2:4])[0]
        ip_packet = ip_packet[:ip_p_lengh]
        ip_header = ip_packet[:ip_h_lengh]
        protocol = unpack('!B', ip_header[9])[0]
        src_ip = socket.inet_ntoa(ip_header[12:16])
        dst_ip = socket.inet_ntoa(ip_header[16:20])
        ip_checksum = unpack('!H', ip_header[10:12])[0]

        if (protocol, src_ip, dst_ip, ip_checksum) != (
                socket.IPPROTO_TCP,
                self.dst_host,
                self.src_host,
                self.ip._calc_checksum(ip_header), ):
            return None

        # Transport Layer
        tcp_packet = ip_packet[ip_h_lengh:]
        tcp_h_length = (unpack('!B', tcp_packet[12])[0] >> 4) * 4
        tcp_header = tcp_packet[:tcp_h_length]
        data = tcp_packet[tcp_h_length:]

        src_port, dst_port = unpack('!HH', tcp_header[:4])
        seq_num, ack_num = unpack('!LL', tcp_header[4:12])
        tcp_checksum = unpack('!H', tcp_header[16:18])[0]
        tcp_flags = unpack('!B', tcp_header[13])[0]

        if (src_port, dst_port, tcp_flags, ack_num, tcp_checksum) != (
                self.dst_port,
                self.src_port,
                flags,
                self.seq_num + self.last_sent_size,
                self._calc_checksum(tcp_packet, self.dst_host, self.src_host),
        ):
            return None

        # Verification passed, accept data
        if tcp_flags & MyTCP.ACK:
            self.seq_num += self.last_sent_size
        self.ack_num = seq_num + len(data)
        return data


if __name__ == '__main__':
    mytcp = MyTCP()
    mytcp.connect(('david.choffnes.com', 80))
    time.sleep(2)
    mytcp.sendall('GET /classes/cs4700fa16/project4.php HTTP/1.1\r\nHost: david.choffnes.com\r\n')

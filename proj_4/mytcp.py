from __future__ import print_function
from struct import pack, unpack
import socket
import random

from myip import MyIP
from utils import calc_checksum, log


class MyTCP:
    '''Customized TCP on transport layer
    '''
    # define TCP flags
    FIN, SYN, RST, PSH, ACK, URG, ECE, CWR = [1 << i for i in xrange(8)]

    def __init__(self):
        self.ip = MyIP()

        self.src_port = self._get_src_port()
        log('Local:', self.ip.src_ip, self.src_port)
        self.dst_port = None
        self.connected = False

        self.seq_num = random.randrange(1 << 32)
        self.ack_num = 0

    def connect(self, netloc):
        dst_host, self.dst_port = netloc
        self.ip.connect(dst_host)
        # TCP handshake
        log('connecting...')
        log('sending: syn')
        self._send('', flags=MyTCP.SYN)
        self.seq_num += 1
        log('waiting: syn, ack')
        self._recv(256, flags=MyTCP.SYN | MyTCP.ACK)
        self.ack_num += 1
        log('sending: ack')
        self._send('', flags=MyTCP.ACK)
        log('connected')
        self.connected = True
        log('status', self.seq_num, self.ack_num)

    def close(self):
        log('disconnecting')
        log('sending: fin')
        self._send('', flags=MyTCP.FIN)
        self.seq_num += 1
        log('waiting: ack')
        self._recv(256, flags=MyTCP.ACK)
        log('waiting: fin')
        self._recv(256, flags=MyTCP.FIN)
        self.ack_num += 1
        log('sending: ack')
        self._send('', flags=MyTCP.ACK)
        log('disconnected')
        self.connected = False

    def sendall(self, data):
        log('sending:', data)
        self._send(data, MyTCP.PSH)
        self.seq_num += len(data)
        self._recv(256, flags=MyTCP.ACK)
        log('sent:', data)

    def recv(self, bufsize):
        data = self._recv(bufsize)
        self.ack_num += len(data)
        self._send('', MyTCP.ACK)
        return data

    def _send(self, data, flags=0):
        if self.connected:
            flags |= MyTCP.ACK

        tcp_packet = self._build_packet(data, flags)
        self.ip.sendto(tcp_packet, self.dst_port)

    def _recv(self, bufsize, flags=0):
        log('looking-for:', self.seq_num, self.ack_num)
        data = None
        while data is None:
            tcp_packet = self.ip.recv(bufsize)
            data = self._filter_packets(tcp_packet, flags)
        return data

    def _build_packet(self, body, flags):
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
        tcp_window = (1 << 16) - 1
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
        checksum = self._calc_checksum(packet, self.ip.src_ip, self.ip.dst_ip)
        packet = packet[:16] + pack('!H', checksum) + packet[18:]

        return packet

    def _calc_checksum(self, packet, src_ip, dst_ip):
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
            socket.inet_aton(src_ip),
            socket.inet_aton(dst_ip),
            0,
            socket.IPPROTO_TCP,
            len(packet), )

        msg = pseudo_header + packet[:16] + pack('!H', 0) + packet[18:]
        return calc_checksum(msg)

    def _get_src_port(self):
        # TODO: ensure a valid port
        return random.randint(10000, 1 << 16 - 1)

    def _filter_packets(self, tcp_packet, flags):
        '''verify the following attributes of received packet
        dst_port, src_port, tcp_checksum, seq_num, flags
        returns the parsed packet if the verification is passed,
        else return None
        '''
        # Transport Layer
        # log('filtering Transport Layer')
        tcp_h_length = (unpack('!B', tcp_packet[12])[0] >> 4) * 4
        tcp_header = tcp_packet[:tcp_h_length]

        src_port, dst_port = unpack('!HH', tcp_header[:4])
        tcp_checksum = unpack('!H', tcp_header[16:18])[0]
        tcp_src_ip = self.ip.dst_ip
        tcp_dst_ip = self.ip.src_ip

        if (src_port, dst_port, tcp_checksum) != (
                self.dst_port,
                self.src_port,
                self._calc_checksum(tcp_packet, tcp_src_ip, tcp_dst_ip), ):
            return None

        # check sequence #
        # log('filtering ack #')
        seq_num, ack_num = unpack('!LL', tcp_header[4:12])
        if not self.connected:
            self.ack_num = seq_num
        seq_match = self.ack_num == seq_num
        if not seq_match:
            return None

        # Check flags
        # log('filtering flags')
        tcp_flags = unpack('!B', tcp_header[13])[0]
        flags_match = (tcp_flags & flags) == flags
        if not flags_match:
            return None

        # Verification passed, accept data
        data = tcp_packet[tcp_h_length:]
        log('accepted', self.seq_num, self.ack_num, len(data))
        return data


# TODO: remove this after testing
def log(*arguments):
    '''Logger in debugging mode
    if option '-d' or '--debug' is given
    import debugging outputs will be printed
    '''
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    if 1:
        print('{}[dbg]{}'.format(WARNING, ENDC), *arguments)


if __name__ == '__main__':
    mytcp = MyTCP()
    mytcp.connect(('david.choffnes.com', 80))
    req = 'GET /classes/cs4700fa16/project4.php HTTP/1.1\n'\
        + 'Host: david.choffnes.com\n\n'
    mytcp.sendall(req)
    while 1:
        print(mytcp.recv(4096))
    mytcp.close()

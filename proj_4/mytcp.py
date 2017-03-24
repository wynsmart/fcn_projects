from __future__ import print_function
from struct import pack, unpack
import socket
import random

from myip import MyIP
from utils import Timer, calc_checksum, log


class MyTCP:
    '''Customized TCP on transport layer
    '''
    # define TCP flags
    FIN, SYN, RST, PSH, ACK, URG, ECE, CWR = [1 << i for i in xrange(8)]

    def __init__(self):
        self.ip = MyIP()

        self.src_port = self._get_src_port()
        log('local:', self.ip.src_ip, self.src_port)
        self.dst_port = None
        self.connected = False

        self.seq_num = random.randrange(1 << 32)
        self.ack_num = 0

        self.cwnd = 1
        self.adv_wnd = None
        self.ssthresh = None

    def connect(self, netloc, retry=3):
        if not retry:
            exit('cannot connect to the host')
        dst_host, self.dst_port = netloc
        self.ip.connect(dst_host)
        # TCP handshake
        log('connecting:', self.ip.dst_ip, self.dst_port)
        log('sending: SYN')
        self._send('', flags=MyTCP.SYN)
        self.seq_num += 1
        log('waiting: SYN, ACK')
        if self._recv(flags=MyTCP.SYN | MyTCP.ACK) is None:
            log('connection failed, retrying...')
            self.connect(netloc, retry=retry - 1)
            return
        self.ack_num += 1
        log('sending: ACK')
        self._send('', flags=MyTCP.ACK)
        log('connected')
        self.connected = True
        log('status', self.seq_num, self.ack_num)

    def close(self):
        log('disconnecting')
        log('sending: FIN')
        self._send('', flags=MyTCP.FIN)
        self.seq_num += 1
        log('waiting: ACK')
        self._recv(flags=MyTCP.ACK)
        log('waiting: FIN')
        self._recv(flags=MyTCP.FIN)
        self.ack_num += 1
        log('sending: ACK')
        self._send('', flags=MyTCP.ACK)
        log('disconnected')
        self.connected = False

    def sendall(self, data, retry=3):
        # TODO: handle 400 bad request
        if not len(data):
            return
        if not retry:
            exit('remote is not responding')
        log('sending:', data)
        init_seq = self.seq_num
        wnd = int(min(self.cwnd, self.adv_wnd))
        flags = MyTCP.PSH if wnd >= len(data) else 0
        bytes_sent = self._send(data[:wnd], flags)
        timer = Timer(60)
        while not timer.timeout():
            if self._recv(flags=MyTCP.ACK, timeout=0.001) is not None:
                self.seq_num += bytes_sent
                # ACK received, increase cwnd
                if self.cwnd < self.ssthresh:
                    self.cwnd += 1
                else:
                    self.cwnd += 1.0 / self.cwnd
            if self.seq_num == (init_seq + bytes_sent):
                # all data has been sent
                break
        else:
            # socket timeout, congestion detected
            self.ssthresh /= 2.0
            self.cwnd = 1

        if self.seq_num == init_seq:
            self.sendall(data, retry=retry - 1)
        else:
            log('sent:', data[:self.seq_num - init_seq])
            self.sendall(data[self.seq_num - init_seq:])

    def recv(self, bufsize=4096):
        log('waiting contents...')
        data = self._recv(bufsize, timeout=3 * 60)
        if data is None:
            exit('remote server stopped responding')
        self._send('', MyTCP.ACK)
        return data

    def _send(self, data, flags=0):
        if self.connected:
            flags |= MyTCP.ACK
        tcp_packet = self._build_packet(data, flags)
        self.ip.sendto(tcp_packet, self.dst_port)
        return len(data)

    def _recv(self, bufsize=4096, flags=0, timeout=60):
        log('looking-for:', self.ack_num)
        # TODO: increase timer to 60
        timer = Timer(timeout)
        data = None
        while data is None and not timer.timeout():
            try:
                tcp_packet = self.ip.recv(bufsize)
                data = self._filter_packets(tcp_packet, flags)
            except:
                pass
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
        return random.randint(40000, (1 << 16) - 1)

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
        log('accepted {} ({} bytes)'.format(seq_num, len(data)))
        self.adv_wnd = unpack('!H', tcp_header[14:16])[0]
        if not self.connected:
            self.ssthresh = self.adv_wnd
        self.ack_num = seq_num + len(data)
        return data

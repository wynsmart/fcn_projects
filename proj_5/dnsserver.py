import socket
import struct
import utils


class MyDNS(object):
    def __init__(self, port, name):
        # TODO: check arguments. if port number is not given the assign random port from 40000-65535
        self.port = port
        self.name = name
        # TODO: traceroute to get latest ip for cs5700cdnproject.ccs.neu.edu
        self.ip = ''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))

    def start(self):
        while 1:
            query, addr = self.sock.recvfrom(4096)
            req_info = Queryparser(query)
            utils.log(req_info.host, 'looking up ...')
            if req_info.opcode != 0:
                utils.log('only opcode 0 is supported')
                continue
            if req_info.host != self.name:
                utils.log('unsopported host name')
                continue
            best_replica_ip = self.get_best_replica(req_info.host)
            response = self._build_packet(req_info, best_replica_ip)
            self.sock.sendto(response, addr)
            utils.log(req_info.host, 'done', best_replica_ip)

    def _build_packet(self, req_info, best_replica_ip):
        '''The header for DNS queries and responses contains field/bits in the
        following diagram taken from [RFC 2136, 2535]:
         0  1  2  3  4  5  6  7  0  1  2  3  4  5  6  7
        +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
        |                      ID                       |
        +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
        |QR|   Opcode  |AA|TC|RD|RA| Z|AD|CD|   RCODE   |
        +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
        |                QDCOUNT/ZOCOUNT                |
        +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
        |                ANCOUNT/PRCOUNT                |
        +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
        |                NSCOUNT/UPCOUNT                |
        +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
        |                    ARCOUNT                    |
        +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+

        The ID field identifies the query and is echoed in the response so
        they can be matched.
        '''

        # Header
        query_id = req_info.transaction_id

        qr = 1 << 15
        opcode = 0 << 11
        aa = 1 << 10
        tc = 0 << 9
        rd = 0 << 8
        ra = 0 << 7
        rcode = 0
        flags = qr + opcode + aa + tc + rd + ra + rcode

        qdcount = 1
        ancount = 1
        nscount = 0
        arcount = 0

        name_ptr = 0xC00C
        rec_type = 1
        rec_class = 1
        ttl = 5
        rdlen = 4
        rd = socket.inet_aton(best_replica_ip)
        answer = struct.pack(
            '!H H H L H 4s',
            name_ptr,
            rec_type,
            rec_class,
            ttl,
            rdlen,
            rd, )

        headers = struct.pack(
            '!H H H H H H',
            query_id,
            flags,
            qdcount,
            ancount,
            nscount,
            arcount, )

        result = headers + req_info.query + answer
        return result

    def get_best_replica(self, host):
        # my EC-2 temp
        return '52.90.80.45'


class Queryparser:
    def __init__(self, query):
        self.transaction_id = struct.unpack('!H', query[:2])[0]
        req_flags = struct.unpack('!H', query[2:4])[0]
        self.opcode = (req_flags >> 11) & 7
        domains = []
        host_raw = query[12:]
        i = 0
        while host_raw[i] != 0:
            l = host_raw[i]
            i += 1
            domains.append(host_raw[i:i + l].decode())
            i += l
        self.host = '.'.join(domains)
        self.query = query[12:]


def main():
    port = utils.args.port
    name = utils.args.name
    MyDNS(port, name).start()


def test():
    port = 44444
    name = 'cs5700cdn.example.com'
    MyDNS(port, name).start()


if __name__ == '__main__':
    utils.load_args()
    if utils.args.test:
        test()
    else:
        main()

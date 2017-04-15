import json
import math
import socket
import struct
import threading
import time

import utils


class MyDNS:
    def __init__(self, port, name):
        self.port = port
        self.name = name
        self.ip = ''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_geos = {}
        self.online_cdns = {}
        self.cache = MyCache(self)

    def start(self):
        try:
            self.sock.bind((self.ip, self.port))
        except Exception as e:
            exit(e)

        print('{:=^60}'.format(' SERVING {} '.format(self.port)))
        print('NAME ->', self.name)
        self.cache.start()
        while 1:
            query, addr = self.sock.recvfrom(4096)
            if b'status' in query:
                self.cdn_report_handler(query, addr[0])
            else:
                DNSLookupHandler(self, query, addr)

    def cdn_report_handler(self, query, addr):
        cdn_info = json.loads(query.decode())
        if cdn_info['status'] and addr not in self.online_cdns:
            self.online_cdns[addr] = utils.get_geo(addr)
            utils.log('CDN+ {}@{} ({} online)'.format(
                addr,
                self.online_cdns[addr],
                len(self.online_cdns), ))
        elif not cdn_info['status'] and addr in self.online_cdns:
            del self.online_cdns[addr]
            utils.log('CDN- {} ({} online)'.format(
                addr,
                len(self.online_cdns), ))


class MyCache(threading.Thread):
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.fname = 'cache.json'
        self.TIME_INTERVAL = 60
        self.daemon = True
        self.load()

    def run(self):
        while 1:
            time.sleep(self.TIME_INTERVAL)
            self.save()

    def load(self):
        try:
            with open(self.fname) as f:
                cache = json.loads(f.read())
        except:
            cache = {}

        self.server.client_geos = cache

    def save(self):
        cache = json.dumps(self.server.client_geos)
        try:
            with open(self.fname, mode='w') as f:
                f.write(cache)
        except Exception as e:
            return utils.err(e)
        utils.log('{:=^30}'.format(' cache saved '))
        utils.log('Clients', self.server.client_geos)
        utils.log('=' * 30)


class DNSLookupHandler(threading.Thread):
    def __init__(self, server, query, client_addr):
        super().__init__()
        self.server = server
        self.query = query
        self.client_addr = client_addr
        self.client = self.client_addr[0]
        self.daemon = True
        self.start()

    def run(self):
        req_info = Queryparser(self.query)
        utils.log(self.client_addr, 'find', req_info.host)
        if req_info.opcode != 0:
            utils.log('only opcode 0 is supported')
            exit()
        if req_info.host != self.server.name:
            utils.log('unsopported host name')
            exit()
        best_replica_ip = self.get_best_replica()
        response = self._build_packet(req_info, best_replica_ip)
        self.server.sock.sendto(response, self.client_addr)
        utils.log(self.client_addr, '-->', best_replica_ip)

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

    def get_best_replica(self):
        '''find shortest geo-location distance in all online CDNs
        '''
        if self.client not in self.server.client_geos:
            self.server.client_geos[self.client] = utils.get_geo(self.client)
        loc1 = self.server.client_geos[self.client]
        dist = {
            cdn: self.calc_dist(loc1, loc2)
            for cdn, loc2 in self.server.online_cdns.items()
        }
        try:
            best_replica_ip = sorted(dist.keys(), key=dist.get)[0]
            return best_replica_ip
        except:
            utils.log('all servers are OFFLINE')
            exit()

    def calc_dist(self, loc1, loc2):
        lat1, lng1 = loc1
        radLat1 = lat1 * (math.pi / 180)
        radLng1 = lng1 * (math.pi / 180)
        lat2, lng2 = loc2
        radLat2 = lat2 * (math.pi / 180)
        radLng2 = lng2 * (math.pi / 180)
        earth_radius = 3959
        diffLat = (radLat1 - radLat2)
        diffLng = (radLng1 - radLng2)
        sinLat = math.sin(diffLat / 2)
        sinLng = math.sin(diffLng / 2)
        a = (sinLat**2) + math.cos(radLat1) * math.cos(radLat2) * (sinLng**2)
        dist = earth_radius * 2 * math.asin(min(1, math.sqrt(a)))
        return dist


class Queryparser:
    def __init__(self, query):
        self.transaction_id = struct.unpack('!H', query[:2])[0]
        req_flags = struct.unpack('!H', query[2:4])[0]
        self.opcode = (req_flags >> 11) & 7
        domains = []
        i = 12
        while query[i] != 0:
            l = query[i]
            i += 1
            domains.append(query[i:i + l].decode())
            i += l
        self.host = '.'.join(domains)
        self.query = query[12:i + 5]


if __name__ == '__main__':
    utils.load_args()
    port = utils.args.port
    name = utils.args.name

    if utils.args.test:
        port = port or 44444
        name = name or utils.DNS_NAME

    if None in (port, name):
        exit('not enough parameters, check help with `-h`')

    MyDNS(port, name).start()

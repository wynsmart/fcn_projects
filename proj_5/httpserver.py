import hashlib
import json
import os
import re
import socket
import threading
import zlib
from time import sleep

import utils


class MyServer:
    def __init__(self, port, origin):
        self.ip = ''
        self.port = port
        self.origin_host = origin
        self.origin_port = utils.CND_ORIGIN_PORT
        utils.log('port   ->', self.port)
        utils.log('origin ->', self.origin_host)
        self.health = True
        self.h_agent = HealthAgent(reporter=self)
        self.cache = MyCache(self)

    def start(self):
        sock = socket.socket()
        try:
            sock.bind((self.ip, self.port))
            sock.listen(5)
        except Exception as e:
            exit(e)

        utils.log('servering ...')
        while 1:
            conn, _ = sock.accept()
            try:
                MyReqHandler(self, conn)
            except Exception as e:
                self.health = False
                utils.log('[BAD HEALTH]', e)
                conn.close()


class MyReqHandler(threading.Thread):
    def __init__(self, serverInstance, connection):
        super().__init__()
        self.daemon = True
        self.server = serverInstance
        self.conn = connection
        self.client = self.conn.getpeername()
        self.start()
        utils.log(self.client, 'connect')

    def run(self):
        raw_request = self.conn.recv(4096)
        self.req = MyRequest(raw_request)
        if self.req.method != 'GET':
            self.done()
            utils.log('only GET method is supported')
            exit()
        utils.log(self.client, self.req.method, self.req.path)
        self.do_GET()

    def do_GET(self):
        res = self.prep_response()
        try:
            self.conn.sendall(res)
        except Exception as e:
            utils.log(e)
        finally:
            self.done()

    def done(self):
        self.conn.close()
        utils.log(self.client, 'done')

    def prep_response(self):
        # check cache
        cached_res = self.server.cache.get(self.req.path)
        if cached_res is not None:
            utils.log(self.client, 'respond with cache')
            return cached_res
        # fetch origin
        utils.log(self.client, 'fetch origin', self.req.path)
        res = self.fetch_origin()
        self.server.cache.add_hotmem(self.req.path, res)
        return res

    def fetch_origin(self):
        host = self.server.origin_host
        port = self.server.origin_port
        raw_request = self.req.forward_raw(host, port)
        res = utils.fetch_origin(raw_request, (host, port))
        return res


class MyRequest:
    def __init__(self, raw_request):
        self.request = raw_request.decode()
        request_info = self.request.split('\r\n')[0]
        try:
            self.method, self.path, _ = request_info.split(' ')
        except Exception:
            self.method = None

    def forward_raw(self, host, port):
        raw_request = re.sub(
            r'^(Host: ).+$',
            r'\1{}:{}'.format(host, port),
            self.request,
            count=1,
            flags=re.MULTILINE, ).encode()
        return raw_request


class MyCache:
    def __init__(self, server):
        # TODO: don't cache dynamic pages such as Special:Random
        self.server = server
        self.dir = './cache'
        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)
        self.std_mem = {}
        self.hot_mem = []
        self.MAX_DISK = 501
        self.MAX_SMEM = 300
        self.MAX_HMEM = 100
        PreCacheAgent(self)

    def get_fname(self, path):
        '''returns hashed path as file name
        '''
        hashed_url = hashlib.md5(path.encode()).hexdigest()
        return '{}/{}'.format(self.dir, hashed_url)

    def add_hotmem(self, path, res):
        '''save response in hot memory
        '''
        res_lite = zlib.compress(res)
        while (len(self.hot_mem)) >= self.MAX_HMEM:
            self.hot_mem.pop(0)
        self.hot_mem.append((path, res_lite))
        utils.log('cached in hot_mem:', path,
                  '[{}bytes]'.format(len(res_lite)))

    def add_stdmem(self, path, res):
        '''save response in standing memory
        '''
        res_lite = zlib.compress(res)
        if len(self.std_mem) < self.MAX_SMEM:
            self.std_mem[path] = res_lite
            utils.log('cached in std_mem:', path,
                      '[{}bytes]'.format(len(res_lite)))

    def add_disk(self, path, res):
        '''save response in disk
        '''
        fname = self.get_fname(path)
        res_lite = zlib.compress(res)
        try:
            with open(fname, mode='wb') as f:
                f.write(res_lite)
            utils.log('cached in disk:', path, '->', fname,
                      '[{}bytes]'.format(len(res_lite)))
        except Exception as e:
            utils.log(e)

    def get(self, path):
        '''get cached response for given path
        1. check in disk persisting cache
        2. check in memory standing cache
        3. check in memory hot cache
        4. return None if not found
        '''
        res = self.get_disk(path)
        if res is not None:
            return res
        res = self.get_stdmem(path)
        if res is not None:
            return res
        res = self.get_hotmem(path)
        if res is not None:
            return res
        return None

    def get_disk(self, path):
        fname = self.get_fname(path)
        try:
            with open(fname, mode='rb') as f:
                res_lite = f.read()
        except Exception as e:
            utils.log(e)
            return None
        res = zlib.decompress(res_lite)
        return res

    def get_stdmem(self, path):
        if path in self.std_mem:
            res_lite = self.std_mem[path]
            res = zlib.decompress(res_lite)
            return res
        else:
            return None

    def get_hotmem(self, path):
        for key_path, res_lite in self.hot_mem:
            if key_path == path:
                res = zlib.decompress(res_lite)
                return res
        return None


class PreCacheAgent(threading.Thread):
    class Worker(threading.Thread):
        def __init__(self, caller, path, save_fn):
            super().__init__()
            self.caller = caller
            self.path = path
            self.save_fn = save_fn
            self.daemon = True
            self.start()

        def run(self):
            self.caller.threads += 1
            host = self.caller.cache.server.origin_host
            port = self.caller.cache.server.origin_port
            request = 'GET {} HTTP/1.1\r\nHost: {}\r\n\r\n'.format(
                self.path,
                '{}:{}'.format(host, port), )
            res = utils.fetch_origin(request.encode(), (host, port))
            self.save_fn(self.path, res)
            self.caller.threads -= 1

    def __init__(self, cache):
        super().__init__()
        self.cache = cache
        self.threads = 0
        self.MAX_THREADS = 10
        self.daemon = True
        self.start()

    def run(self):
        '''pre-cache in disk and in standing memory content
        '''
        utils.log('PRE-CACHING [start]')
        paths = utils.import_paths()
        for i, path in enumerate(paths):
            if i >= self.cache.MAX_DISK + self.cache.MAX_SMEM:
                break

            self.wait_slot()
            if i < self.cache.MAX_DISK:
                if self.cache.get_disk(path) is None:
                    PreCacheAgent.Worker(self, path, self.cache.add_disk)
            else:
                if self.cache.get_stdmem(path) is None:
                    PreCacheAgent.Worker(self, path, self.cache.add_stdmem)

        self.wait_sync()
        utils.log('PRE-CACHING [finished]')

    def wait_slot(self):
        while self.threads >= self.MAX_THREADS:
            pass

    def wait_sync(self):
        while self.threads:
            pass


class HealthAgent(threading.Thread):
    def __init__(self, reporter=None):
        super().__init__()
        self.daemon = True
        self.reporter = reporter
        self.geo_loc = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))
        self.start()

    def run(self):
        time_interval = 5 if self.reporter.health else 20
        while 1:
            info = {'status': self.reporter.health}
            data = json.dumps(info).encode()
            self.sock.sendto(data, (utils.DNS_HOST, self.reporter.port))
            sleep(time_interval)
            self.reporter.health = True


if __name__ == '__main__':
    utils.load_args()
    port = utils.args.port
    origin = utils.args.origin
    if utils.args.test:
        port = port or 55555
        origin = origin or utils.CDN_ORIGIN_HOST
    MyServer(port, origin).start()

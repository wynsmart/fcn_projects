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
        self.originHost = origin
        self.originPort = 8080
        self.maxConn = 9999
        self.threads = []
        self.lock = MyFileLock()
        self.cache = MyCache(self.lock)
        utils.log('port   ->', self.port)
        utils.log('origin ->', self.originHost)
        self.h_agent = HealthAgent(reporter=self)

    def start(self):
        sock = socket.socket()
        try:
            sock.bind((self.ip, self.port))
            sock.listen(5)
        except Exception as e:
            exit(e)

        utils.log('servering ...')
        while 1:
            self.threads = [t for t in self.threads if t.is_alive()]
            if len(self.threads) >= self.maxConn:
                continue
            conn, _ = sock.accept()
            handler = MyReqHandler(self, conn)
            self.threads.append(handler)


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
        cached_res = self.server.cache.get(self.req.path)
        if cached_res is not None:
            utils.log(self.client, 'respond with cache')
            return cached_res
        # fetch origin
        utils.log(self.client, 'fetch origin', self.req.path)
        res = self.fetch_origin()
        self.server.cache.set(self.req.path, res)
        return res

    def fetch_origin(self):
        # TODO: retry when failure with timeouted socket
        host = self.server.originHost
        port = self.server.originPort
        raw_request = self.req.forward_raw(host, port)
        sock = socket.socket()
        sock.connect((host, port))
        sock.sendall(raw_request)
        res = bytes()
        while not self.res_complete(res):
            res += sock.recv(4096)
        sock.close()
        return res

    def res_complete(self, res):
        '''Check whether a response is complete
        If response is chunked encoded, then check the ending bytes;
        Else if response has Content-Length, then check current body length;
        '''
        try:
            headers, body = res.split(b'\r\n\r\n', maxsplit=1)
        except:
            return False

        if b'Transfer-Encoding: chunked' in headers:
            return body.endswith(b'0\r\n\r\n')

        mclength = re.search(r'Content-Length: (\d+)', headers.decode())
        if mclength is None:
            return False

        clength = int(mclength.group(1))
        return len(body) == clength


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
    # TODO: Implement in memory cache as well

    def __init__(self, lock):
        # TODO: don't cache dynamic pages such as Special:Random
        self.lock = lock
        self.dir = './cache'
        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)

    def get_fname(self, path):
        hashed_url = hashlib.md5(path.encode()).hexdigest()
        return '{}/{}'.format(self.dir, hashed_url)

    def set(self, path, res):
        # TODO: test and handle db concurrent writes
        fname = self.get_fname(path)
        res_lite = zlib.compress(res)
        self.lock.acquire(fname)
        try:
            with open(fname, mode='wb') as f:
                f.write(res_lite)
            utils.log('cached:', path, '->', fname)
        except Exception as e:
            utils.log(e)
        finally:
            self.lock.release(fname)

    def get(self, path):
        fname = self.get_fname(path)
        self.lock.acquire(fname)
        try:
            with open(fname, mode='rb') as f:
                res_lite = f.read()
        except Exception as e:
            utils.log(e)
            return None
        finally:
            self.lock.release(fname)
        res = zlib.decompress(res_lite)
        return res

    def drop(self, path):
        fname = self.get_fname(path)
        self.lock.acquire(fname)
        try:
            os.remove(fname)
        except Exception as e:
            utils.log(e)
        self.lock.release(fname)


class MyFileLock:
    def __init__(self):
        self.locks = set()

    def acquire(self, fname):
        while fname in self.locks:
            utils.log('xxx')
            pass
        self.locks.add(fname)
        assert fname in self.locks

    def release(self, fname):
        self.locks.remove(fname)


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
        if self.reporter:
            self.report()
        elif self.receiver:
            self.receive()

    def report(self):
        TIME_INTERVAL = 5
        while 1:
            info = {'status': True}
            data = json.dumps(info).encode()
            self.sock.sendto(data, (utils.DNS_HOST, self.reporter.port))
            sleep(TIME_INTERVAL)


if __name__ == '__main__':
    utils.load_args()
    port = utils.args.port
    origin = utils.args.origin
    if utils.args.test:
        port = port or 55555
        origin = origin or utils.CDN_ORIGIN
    MyServer(port, origin).start()

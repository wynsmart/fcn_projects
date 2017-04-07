from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import utils
import re
import threading
import socket
import zlib
import hashlib
import os


class MyServer:
    def __init__(self, port, origin):
        self.ip = ''
        self.port = port
        self.originHost = origin
        self.originPort = 8080
        self.maxConn = 9999
        self.threads = []
        self.cache = MyCache()

    def start(self):
        sock = socket.socket()
        try:
            sock.bind((self.ip, self.port))
            sock.listen(5)
            utils.log('HTTP Server -> {}'.format(sock.getsockname()))
        except Exception as e:
            exit(e)

        while 1:
            self.threads = [t for t in self.threads if t.is_alive()]
            if len(self.threads) >= self.maxConn:
                continue
            conn, _ = sock.accept()
            handler = MyReqHandler(self, conn)
            handler.start()
            # utils.log(conn.getpeername(), 'connect')
            # handler = MyReqHandler(self, conn)
            # if handler.method != 'GET':
            #     handler.done()
            #     utils.log('only GET method is supported')
            #     continue
            # t = threading.Thread()
            # t.daemon = True
            # t.run = handler.do_GET
            # t.start()
            self.threads.append(handler)


class MyReqHandler(threading.Thread):
    def __init__(self, serverInstance, connection):
        super().__init__()
        self.daemon = True
        self.server = serverInstance
        self.conn = connection
        self.client = self.conn.getpeername()
        utils.log(self.client, 'connect')

    def run(self):
        raw_request = self.conn.recv(4096)
        self.req = MyRequest(raw_request)
        utils.log(self.client, self.req.method, self.req.path)
        if self.req.method != 'GET':
            self.done()
            utils.log('only GET method is supported')
            exit()
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
        if cached_res is None:
            res = self.fetch_origin()
            self.server.cache.set(self.req.path, res)
            return res
        else:
            utils.log(self.client, 'respond with cache')
            return cached_res

    def fetch_origin(self):
        host = self.server.originHost
        port = self.server.originPort
        raw_request = self.req.forward_raw(host, port)
        sock = socket.socket()
        sock.connect((host, port))
        sock.sendall(raw_request)
        res = bytes()
        while not self.res_complete(res):
            res += sock.recv(4096)
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
    def __init__(self):
        # TODO: don't cache dynamic pages such as Special:Random
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
        with open(fname, mode='wb') as f:
            f.write(res_lite)
        utils.log('cached:', path, fname)

    def get(self, path):
        fname = self.get_fname(path)
        try:
            with open(fname, mode='rb') as f:
                res_lite = f.read()
        except Exception as e:
            utils.log(e)
            return None
        res = zlib.decompress(res_lite)
        return res

    def drop(self, url):
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        c.execute("""
        delete from `{}` where `url`=?
        """.format(self.tablename), (url, ))
        conn.commit()


def main():
    port = utils.args.port
    origin = utils.args.origin
    MyServer(port, origin).start()


def test():
    port = 55555
    origin = 'ec2-54-166-234-74.compute-1.amazonaws.com'
    MyServer(port, origin).start()


if __name__ == '__main__':
    utils.load_args()
    if utils.args.test:
        test()
    else:
        main()

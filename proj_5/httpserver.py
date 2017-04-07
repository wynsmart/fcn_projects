from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import utils
import threading
import socket
import json
import zlib
import sqlite3


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
            utils.log(conn.getpeername(), 'connect')
            handler = MyReqHandler(self, conn)
            if handler.method != 'GET':
                handler.done()
                utils.log('only GET method is supported')
                continue
            t = threading.Thread()
            t.daemon = True
            t.run = handler.do_GET
            t.start()
            self.threads.append(t)


class MyReqHandler:
    def __init__(self, serverInstance, connection):
        self.server = serverInstance
        self.conn = connection
        self.client = self.conn.getpeername()
        request = self.conn.recv(4096).decode()
        req_essential = request.split('\r\n')[0]
        utils.log(self.client, req_essential)
        try:
            self.method, self.path, self.version = req_essential.split(' ')
            # utils.log(self.method, self.path, self.version)
        except Exception:
            self.method = None

    def do_GET(self):
        res = self.prep_response()
        try:
            self.send_response(res.code)
            self.send_headers(res.headers)
            self.send_body(res.body)
        except Exception as e:
            utils.log(e)
        finally:
            self.done()

    def send_response(self, code):
        reason_phrases = {
            100: 'Continue',
            101: 'Switching Protocols',
            200: 'OK',
            201: 'Created',
            202: 'Accepted',
            203: 'Non-Authoritative Information',
            204: 'No Content',
            205: 'Reset Content',
            206: 'Partial Content',
            300: 'Multiple Choices',
            301: 'Moved Permanently',
            302: 'Found',
            303: 'See Other',
            304: 'Not Modified',
            305: 'Use Proxy',
            307: 'Temporary Redirect',
            400: 'Bad Request',
            401: 'Unauthorized',
            402: 'Payment Required',
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            406: 'Not Acceptable',
            407: 'Proxy Authentication Required',
            408: 'Request Time-out',
            409: 'Conflict',
            410: 'Gone',
            411: 'Length Required',
            412: 'Precondition Failed',
            413: 'Request Entity Too Large',
            414: 'Request-URI Too Large',
            415: 'Unsupported Media Type',
            416: 'Requested range not satisfiable',
            417: 'Expectation Failed',
            500: 'Internal Server Error',
            501: 'Not Implemented',
            502: 'Bad Gateway',
            503: 'Service Unavailable',
            504: 'Gateway Time-out',
            505: 'HTTP Version not supported',
        }
        res = '{} {} {}\r\n'.format(self.version, code, reason_phrases[code])
        self.write(res)

    def send_headers(self, headers):
        for k, v in headers.items():
            self.write('{}: {}\r\n'.format(k, v))
        self.write('\r\n')

    def send_body(self, body):
        self.write(body)

    def write(self, data):
        data_bytes = data if type(data) is type(bytes()) else data.encode()
        self.conn.sendall(data_bytes)

    def done(self):
        self.conn.close()
        utils.log(self.client, 'done')

    def prep_response(self):
        cached_res = self.server.cache.get(self.path)
        if cached_res is None:
            res = self.fetch_origin()
            self.server.cache.set(self.path, res)
            return res
        else:
            utils.log(self.client, 'respond with cache')
            return cached_res

    def fetch_origin(self):
        url = 'http://{}:{}{}'.format(
            self.server.originHost,
            self.server.originPort,
            self.path, )
        utils.log(self.client, url)
        try:
            f = urlopen(url)
        except HTTPError as e:
            return MyResponse(e.code, e.headers, e.reason.encode())
        except URLError as e:
            utils.log(e.reason)
            exit(e.reason)

        res = MyResponse(f.getcode(), f.info(), f.read())
        return res


class MyResponse:
    def __init__(self, code, headers, body_bytes):
        self.code = code
        self.headers = headers
        self.body = body_bytes
        if self.headers.get('Transfer-Encoding') == 'chunked':
            # remove Chunked Transfer-Encoding from header
            del self.headers['Transfer-Encoding']


class MyCache:
    # TODO: Implement in memory cache as well
    def __init__(self):
        # TODO: don't cache dynamic pages such as Special:Random
        self.dbname = 'cache.db'
        self.tablename = 'Cache'
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        c.execute("""
        create table if not exists `{}` (
        	`url` text primary key,
        	`code` integer not null,
        	`headers` blob not null,
        	`body` blob not null
        )
        """.format(self.tablename))
        conn.commit()

    def set(self, path, res):
        # TODO: test and handle db concurrent writes
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        headers = {k: v for k, v in res.headers.items()}
        headers_json = json.dumps(headers, separators=(',', ':'))
        headers_lite = zlib.compress(headers_json.encode())
        body_lite = zlib.compress(res.body)
        subs = (path, res.code, headers_lite, body_lite)
        c.execute("""
        replace into `{}` (`url`, `code`, `headers`, `body`) values (?,?,?,?)
        """.format(self.tablename), subs)
        conn.commit()
        utils.log('cached:', path)

    def get(self, path):
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        c.execute("""
        select `code`, `headers`, `body` from `{}` where `url`=?
        """.format(self.tablename), (path, ))
        cache = c.fetchone()
        if cache is None:
            return None
        code, headers_lite, body_lite = cache
        headers_json = zlib.decompress(headers_lite).decode()
        headers = json.loads(headers_json)
        body = zlib.decompress(body_lite)
        # utils.log(code, headers, len(body))
        return MyResponse(code, headers, body)

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

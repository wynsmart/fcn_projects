from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import threading
import socket
import utils


class MyServer:
    def __init__(self, port, origin):
        self.ip = ''
        self.port = port
        self.originHost = origin
        self.originPort = 8080
        self.maxConn = 9999
        self.threads = []

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
        self.send_response(res.code)
        self.send_headers(res.headers)
        self.send_body(res.body)
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
        self.conn.sendall(data.encode())

    def done(self):
        self.conn.close()
        utils.log(self.client, 'done')

    def prep_response(self):
        # TODO: managing cache
        return self.fetch_origin()

    def fetch_origin(self):
        url = 'http://{}:{}{}'.format(
            self.server.originHost,
            self.server.originPort,
            self.path, )
        utils.log(self.client, url)
        try:
            f = urlopen(url)
        except HTTPError as e:
            return MyResponse(e.code, e.headers, e.reason)
        except URLError as e:
            utils.log(e.reason)
            exit(e.reason)

        res = MyResponse(f.getcode(), f.info(), f.read().decode())
        return res


class MyResponse:
    def __init__(self, code, headers, body):
        self.code = code
        self.headers = headers
        self.body = body
        if self.headers.get('Transfer-Encoding') == 'chunked':
            # remove Chunked Transfer-Encoding from header
            del self.headers['Transfer-Encoding']


def main():
    port = int(utils.args.port)
    origin = utils.args.origin
    MyServer(port, origin).start()


def test():
    port = 45678
    origin = 'ec2-54-166-234-74.compute-1.amazonaws.com'
    MyServer(port, origin).start()


if __name__ == '__main__':
    utils.load_args()
    if utils.args.test:
        test()
    else:
        main()

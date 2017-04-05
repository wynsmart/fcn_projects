from http.server import (
    HTTPServer,
    BaseHTTPRequestHandler, )
from urllib.request import (urlopen, )
from urllib.error import (URLError, )
import socket
import utils


class MyServer(HTTPServer):
    def __init__(self, port, origin):
        self.ip = ''
        self.port = port
        self.httpd = HTTPServer((self.ip, self.port), MyReqHandler)
        self.httpd.originHost = origin
        self.httpd.originPort = 8080

    def start(self):
        utils.log('HTTP Server -> {}:{}'.format(self.httpd.server_name,
                                                self.httpd.server_port))
        self.httpd.serve_forever()


class MyReqHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        utils.log('origin:', self.server.originHost, self.server.originPort)
        utils.log('requesting:', self.path)
        res = self.prep_response()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=UTF-8')
        self.end_headers()
        self.wfile.write(res)

    def prep_response(self):
        url = 'http://{}:{}{}'.format(self.server.originHost,
                                      self.server.originPort, self.path)
        try:
            f = urlopen(url)
        except URLError as e:
            utils.log(e.reason)
            return None

        return f.read()


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

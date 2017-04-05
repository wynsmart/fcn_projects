from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
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
        self.send_response(res.code)
        self.send_headers(res.headers)
        self.wfile.write(res.body.encode())

    def send_headers(self, headers):
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()

    def prep_response(self):
        return self.fetch_origin()

    def fetch_origin(self):
        url = 'http://{}:{}{}'.format(self.server.originHost,
                                      self.server.originPort, self.path)
        utils.log('fetching origin:', url)
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

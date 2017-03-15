from __future__ import print_function
import socket
import re
from urlparse import urlparse

from utils import log


class MyHTTP:
    '''Wrapped Socket class to simplify the HTTP APIs
    '''

    def res_complete(self, res):
        '''Check whether a response is complete
        If response has Content-Length, then check current body length;
        Else if response is chunked encoded, then check the ending bytes;
        '''
        match_len = re.search(r'Content-Length: (\d+)', res)
        if match_len:
            content_len = int(match_len.group(1))
            body_offset = res.find('\r\n\r\n') + 4
            if body_offset >= 4 and body_offset + content_len <= len(res):
                return True
        elif 'Transfer-Encoding: chunked' in res and '0\r\n\r\n' in res:
            return True

        return False

    # wrapper for HTTP send and receive functions
    def _http(self, netloc, req):
        # create socket and connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if ':' not in netloc:
            netloc += ':80'
        host, port = netloc.split(':', 1)
        if not host:
            exit('Cannot get URL, hostname cannot be empty')
        try:
            port = int(port)
        except Exception as e:
            exit('Cannot get URL, invalid port number')

        sock.connect((host, port))

        # send request
        # sock.sendall(req.encode())
        sock.sendall(req)

        # get response
        BUFFER_SIZE = 256
        res = ''
        data = True
        while not self.res_complete(res) and data:
            data = sock.recv(BUFFER_SIZE)
            res += data
        # log('received:', len(res))
        sock.close()
        # res = res.decode('utf8')
        return self.parse_res(res)

    def _flatten_dict(self, d, item, separator):
        return separator.join(item.format(key, d[key]) for key in d)

    # get parameters from the HTTP wrapper header
    def genHeaders(self, headers):
        return self._flatten_dict(headers, '{}: {}', '\n')

    # HTTP GET method
    def get(self, url):
        url_components = urlparse(url)

        # exit when protocol is not http
        if url_components.scheme != 'http':
            exit('Only HTTP is supported')

        headers = {'Host': url_components.netloc, }
        path = url_components.path or '/'
        req = 'GET {} HTTP/1.1\n{}\n\n'.format(path, self.genHeaders(headers))
        # log(req)
        res = self._http(url_components.netloc, req)

        # exit when status is not 200
        if res['status'] != 200:
            exit('Error, HTTP status {}'.format(res['status']))

        # save target file
        save_file = url_components.path.split('/')[-1] or 'index.html'
        with open('tmp/' + save_file, mode='w') as f:
            f.write(res['body'])

    # parse the received data from server into given parameters
    def parse_res(self, res):
        status = int(res[9:12])
        headers, body = res.split('\r\n\r\n', 1)
        if 'Transfer-Encoding: chunked' in headers:
            body = self.decode_chunked(body)
        return {
            'status': status,
            'headers': headers,
            'body': body,
        }

    def decode_chunked(self, body):
        '''decode chunked http response
        reference -> https://en.wikipedia.org/wiki/Chunked_transfer_encoding
        '''
        return re.sub(r'\r\n[0-9a-f]+\s*\r\n', '', '\r\n' + body[:-2])

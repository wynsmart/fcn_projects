from __future__ import print_function
import re
from urlparse import urlparse
import socket

from utils import log
from mytcp import MyTCP


class MyHTTP:
    '''Customized HTTP on application layer
    '''

    def __init__(self):
        self.tcp = socket.socket
        self.tcp = MyTCP

    def get(self, url):
        '''HTTP GET method, main public API
        '''
        url_components = urlparse(url)

        # exit when protocol is not http
        if url_components.scheme != 'http':
            exit('Only HTTP is supported')

        path = url_components.path or '/'
        headers = self.genHeaders({'Host': url_components.netloc, })
        req = 'GET {} HTTP/1.1\n{}\n\n'.format(path, headers)
        # log(req)
        res = self._http(url_components.netloc, req)

        # exit when status is not 200
        if res['status'] != 200:
            exit('Error, HTTP status {}'.format(res['status']))

        # save target file
        save_file = url_components.path.split('/')[-1] or 'index.html'
        with open(save_file, mode='w') as f:
            f.write(res['body'])

    def _http(self, netloc, req):
        '''http communicator over tcp layer
        '''
        if ':' not in netloc:
            netloc += ':80'
        host, port = netloc.split(':', 1)
        if not host:
            exit('Cannot get URL, hostname cannot be empty')
        try:
            port = int(port)
        except:
            exit('Cannot get URL, invalid port number')

        # create socket and connect
        tcp = self.tcp()
        tcp.connect((host, port))

        # send request
        tcp.sendall(req)

        # get response
        res = ''
        data = True
        buff_size = 4096
        while not self.res_complete(res) and data:
            data = tcp.recv(buff_size)
            res += data
        # log('received:', len(res))
        tcp.close()

        return self.parse_res(res)

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

    def genHeaders(self, headers):
        '''generate raw request headers from given dictionary
        '''
        return self._flatten_dict(headers, '{}: {}', '\n')

    def _flatten_dict(self, d, item, separator):
        return separator.join(item.format(key, d[key]) for key in d)

    def parse_res(self, res):
        '''parse the received data from server into http components
        '''
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

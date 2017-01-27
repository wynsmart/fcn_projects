import socket
import re

from utils import log


class MyHTTP:
    '''Wrapped Socket class to simplify the HTTP APIs
    '''

    def __init__(self, hostname, port=80):
        self.hostname = hostname
        self.port = port

    def _http(self, raw):
        # create socket and connect
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.hostname, self.port))

        # send request
        self.socket.sendall(raw.encode())

        # get response
        # TODO: reduce the choking time
        BUFFER_SIZE = 1024
        res = ''
        while 1:
            data = self.socket.recv(BUFFER_SIZE).decode()
            if not data:
                break
            res += data
        log('received:', len(res))
        return res

    def _flatten_dict(self, d, item, separator):
        return separator.join(item.format(key, d[key]) for key in d)

    def genHeaders(self, headers):
        return self._flatten_dict(headers, '{}: {}', '\n')

    def genCookies(self, cookies):
        return self._flatten_dict(cookies, '{}={}', '; ')

    def genBody(self, body_dict):
        return self._flatten_dict(body_dict, '{}={}', '&')

    def get(self, path, cookies=None):
        headers = {'Host': self.hostname, }
        if cookies:
            headers['Cookie'] = self.genCookies(cookies)
        req = 'GET {} HTTP/1.1\n{}\n\n'.format(path, self.genHeaders(headers))
        log(req)
        return self._http(req)

    def post(self, path, body, cookies):
        body = self.genBody(body)
        headers = {
            'Host': self.hostname,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': len(body),
        }
        if cookies:
            headers['Cookie'] = self.genCookies(cookies)
        req = 'POST {} HTTP/1.1\n{}\n\n{}'.format(path,
                                                  self.genHeaders(headers),
                                                  body)
        log(req)
        return self._http(req)


class MyPaw:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.hostname = 'cs5700sp17.ccs.neu.edu'
        self.http = MyHTTP(self.hostname)
        self.cookies = {}
        self.login_page = '/accounts/login/?next=/fakebook/'

    def updateCookies(self, res):
        cookies = re.findall(r'Set-Cookie: ([^=]+)=([^;]+)', res)
        for key, val in cookies:
            self.cookies[key] = val
        log(self.cookies)

    def login(self):
        # get csrftoken
        res = self.http.get('/accounts/login/?next=/fakebook/')
        self.updateCookies(res)

        # log in
        form = {
            'username': self.username,
            'password': self.password,
            'csrfmiddlewaretoken': self.cookies['csrftoken'],
            'next': '/fakebook/',
        }
        res = self.http.post(self.login_page, form, self.cookies)
        log(res)

        # update session id
        self.updateCookies(res)

        log('login succeeded as {}'.format(self.username))

    def fetch(self, path):
        '''Returns the page source of the given relative path
        '''
        if not self.cookies:
            self.login()

        # TODO: there might be exceptions
        res = self.http.get(path, self.cookies)

        return res

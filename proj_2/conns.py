import socket
import re

from utils import log


class MyHTTP:
    '''Wrapped Socket class to simplify the HTTP APIs
    '''

    def __init__(self, hostname, port=80):
        self.hostname = hostname
        self.port = port

    def res_complete(self, res):
        # If we got the Content-Length, we test whether the body is complete
        # by its length; If we didn't get the Content-Length, assume that the
        # response is incomplete
        match_len = re.search(r'Content-Length: (\d+)', res)
        if match_len:
            content_len = int(match_len.group(1))
            body_offset = res.find('\r\n\r\n') + 4
            if body_offset >= 4 and body_offset + content_len <= len(res):
                return True

        return False

    def _http(self, raw):
        # create socket and connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.hostname, self.port))

        # send request
        sock.sendall(raw.encode())

        # get response
        BUFFER_SIZE = 1024
        res = ''
        while not self.res_complete(res):
            data = sock.recv(BUFFER_SIZE).decode()
            res += data
            if not data:
                break
        # log('received:', len(res))
        sock.close()
        return self.parse_res(res)

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
        # log(req)
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
        # log(req)
        return self._http(req)

    def parse_res(self, res):
        status = int(res[9:12])
        headers, body = res.split('\r\n\r\n', maxsplit=1)
        return {
            'status': status,
            'headers': headers,
            'body': body,
        }


class MyPaw:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.hostname = 'cs5700sp17.ccs.neu.edu'
        self.http = MyHTTP(self.hostname)
        self.cookies = {}
        self.login_page = '/accounts/login/?next=/fakebook/'

    def updateCookies(self, res):
        cookies = re.findall(r'Set-Cookie: ([^=]+)=([^;]+)', res['headers'])
        for key, val in cookies:
            self.cookies[key] = val
        # log(self.cookies)

    def login(self, retries=3):
        if retries < 0:
            print('[Login Failed] Incorrect username or password')
            exit()

        log('logging in as {}'.format(self.username))

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
        # log('zzz', res)

        # update session id
        self.updateCookies(res)

        # retry if login failed
        if 'Please enter a correct username and password.' in res['body']:
            self.login(retries=retries - 1)

    def fetch(self, path):
        '''Returns the page source of the given relative path
        '''
        if not self.cookies:
            self.login()

        res = False
        while (not res) or (res['status'] == 500):
            res = self.http.get(path, self.cookies)
            if res['status'] == 403 or res['status'] == 404:
                return ''
            elif res['status'] == 301:
                path_pattern = r'Location: http://{}(.+)'.format(self.hostname)
                url_match = re.search(path_pattern, res['headers'])
                if url_match:
                    path = url_match.group(1)
                    res = False
            elif res['status'] == 302:
                if re.search(r'Location: .*login.*', res['headers']):
                    log('login required, retrying...')
                    self.login()
                    res = False

        return res['body']

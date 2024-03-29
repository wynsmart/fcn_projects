import socket
import re

from utils import log


class MyHTTP:
    '''Wrapped Socket class to simplify the HTTP APIs
    '''

    # initialize the wrapper socket connection parameters;
    # default port is 80 unless specified
    def __init__(self, hostname, port=80):
        self.hostname = hostname
        self.port = port

    def res_complete(self, res):
        # An </html> tag in response body is considered complete. Or if we got
        # the Content-Length, we test whether the body is complete by its
        # length; If we didn't get the Content-Length, assume that the
        # response is incomplete
        if '</html>' in res:
            return True

        match_len = re.search(r'Content-Length: (\d+)', res)
        if match_len:
            content_len = int(match_len.group(1))
            body_offset = res.find('\r\n\r\n') + 4
            if body_offset >= 4 and body_offset + content_len <= len(res):
                return True

        return False

    # wrapper for HTTP send and receive functions
    def _http(self, raw):
        # create socket and connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.hostname, self.port))

        # send request
        sock.sendall(raw.encode())

        # get response
        BUFFER_SIZE = 256
        res = ''
        data = True
        while not self.res_complete(res) and data:
            data = sock.recv(BUFFER_SIZE).decode()
            res += data
        # log('received:', len(res))
        sock.close()
        return self.parse_res(res)

    def _flatten_dict(self, d, item, separator):
        return separator.join(item.format(key, d[key]) for key in d)

    # get parameters from the HTTP wrapper header
    def genHeaders(self, headers):
        return self._flatten_dict(headers, '{}: {}', '\n')

    def genCookies(self, cookies):
        return self._flatten_dict(cookies, '{}={}', '; ')

    def genBody(self, body_dict):
        return self._flatten_dict(body_dict, '{}={}', '&')

    # HTTP GET method
    def get(self, path, cookies=None):
        headers = {'Host': self.hostname, }
        if cookies:
            headers['Cookie'] = self.genCookies(cookies)
        req = 'GET {} HTTP/1.1\n{}\n\n'.format(path, self.genHeaders(headers))
        # log(req)
        return self._http(req)

    # HTTP POST method
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

    # parse the received data from server into given parameters
    def parse_res(self, res):
        status = int(res[9:12])
        headers, body = res.split('\r\n\r\n', maxsplit=1)
        return {
            'status': status,
            'headers': headers,
            'body': body,
        }


class MyPaw:
    '''High level APIs to login and crawl on Fakebook with the help of MyHTTP
    '''
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.hostname = 'cs5700sp17.ccs.neu.edu'
        self.http = MyHTTP(self.hostname)
        self.cookies = {}
        self.login_page = '/accounts/login/?next=/fakebook/'

    # obtain the cookie value from the header after successful login
    def updateCookies(self, res):
        cookies = re.findall(r'Set-Cookie: ([^=]+)=([^;]+)', res['headers'])
        for key, val in cookies:
            self.cookies[key] = val
        # log(self.cookies)

    def login(self, retries=3):
        '''Login with credentials, returns True if succeeded, else False
        '''
        if retries < 0:
            return False

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

        # check login results, retry if login failed
        failure_msg = 'Please enter a correct username and password.'
        is_failed = failure_msg in res['body']
        return self.login(retries=retries - 1) if is_failed else True

    # fetches the page source of a given URL path
    def fetch(self, path):
        '''Returns the page source of the given relative path
        '''

        # handle HTTP error messages
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

        return res['body']

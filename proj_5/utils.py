import argparse
import json
import re
import socket
import subprocess
import time

args = None

PAGES = 'pages'
DNS_HOST = 'cs5700cdnproject.ccs.neu.edu'
# DNS_HOST = 'login.ccs.neu.edu'
DNS_NAME = 'cs5700cdn.example.com'
CDN_ORIGIN_HOST = 'ec2-54-166-234-74.compute-1.amazonaws.com'
CND_ORIGIN_PORT = 8080
CDN_HOSTS = [
    'ec2-52-90-80-45.compute-1.amazonaws.com',  # N. Virginia
    'ec2-54-183-23-203.us-west-1.compute.amazonaws.com',  # N. California
    'ec2-54-70-111-57.us-west-2.compute.amazonaws.com',  # Oregon
    'ec2-52-215-87-82.eu-west-1.compute.amazonaws.com',  # Ireland
    'ec2-52-28-249-79.eu-central-1.compute.amazonaws.com',  # Frankfurt
    'ec2-54-169-10-54.ap-southeast-1.compute.amazonaws.com',  # Singapore
    'ec2-52-62-198-57.ap-southeast-2.compute.amazonaws.com',  # Sydney
    'ec2-52-192-64-163.ap-northeast-1.compute.amazonaws.com',  # Tokyo
    'ec2-54-233-152-60.sa-east-1.compute.amazonaws.com',  # Sao Paolo
]


def load_args():
    '''Parse the arguments with argparse utility
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-t', '--test', action='store_true')
    parser.add_argument('-p', '--port', type=int, default=0)
    parser.add_argument('-n', '--name')
    parser.add_argument('-o', '--origin')
    parser.add_argument('-m', '--mode')
    parser.add_argument('-u', '--username')
    parser.add_argument('-i', '--keyfile')

    global args
    args = parser.parse_args()


def log(*arguments, override=False):
    '''Logger in debugging mode
    if option '-d' or '--debug' is given
    import debugging outputs will be printed
    '''
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    tm = '{0.tm_hour:02}:{0.tm_min:02}:{0.tm_sec:02}'.format(time.localtime())
    if args.debug:
        end = '\r' if override else '\n'
        print('{}[{}]{}'.format(WARNING, tm, ENDC), *arguments, end=end)


def hexrepr(msg):
    '''Returns the hex representation of given message
    '''
    return ' '.join('{:02x}'.format(x) for x in msg)


def hexprint(msg):
    '''Prints Wireshark like hex representation of given msg
    '''
    for i in range(0, len(msg), 16):
        print('{}   {}'.format(
            hexrepr(msg[i:i + 8]),
            hexrepr(msg[i + 8:i + 16]), ))


def get_geo(ip):
    if ip == '127.0.0.1':
        return 0, 0
    url = 'http://ipinfo.io/{}/geo'
    res = subprocess.check_output(['curl', '-s', url.format(ip)])
    geo = json.loads(res.decode())
    return tuple(float(l) for l in geo['loc'].split(','))


def fetch_origin(raw_request, to_addr):
    while 1:
        sock = socket.socket()
        sock.connect(to_addr)
        sock.sendall(raw_request)
        res = bytes()
        while not res_complete(res):
            res += sock.recv(4096)
        sock.close()
        if res[9] in b'234':
            return res


def res_complete(res):
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


def extract_paths():
    with open(PAGES, mode='w') as outf:

        fname = 'popular_raw.html'
        with open(fname, encoding='utf8') as inf:
            html = inf.read()

        paths = ['/']
        paths += re.findall(r'a href="([^"]+)" title', html)
        outf.writelines([path + '\n' for path in paths])


def import_paths():
    with open(PAGES) as f:
        return f.read().split()


if __name__ == '__main__':
    extract_paths()

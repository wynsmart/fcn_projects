import re
import threading
from time import sleep
from urllib.request import urlopen


def parse_urls(fname):
    with open(fname, encoding='utf8') as f:
        html = f.read()

    for i in range(500):
        m = re.search(r'a href="([^"]+)', html, re.M)
        html = html[m.end(1):]
        path = m.group(1)
        m = re.search(r'td align="right">([0-9,]+)', html, re.M)
        html = html[m.end(1):]
        visits = int(m.group(1).replace(',', ''))
        print(visits, path)
        yield path


class P(threading.Thread):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.start()
        global ts
        ts += 1

    def run(self):
        download(self.path)
        global ts
        ts -= 1


def download(path):
    try:
        urlopen('http://localhost:55555{}'.format(path))
    except:
        pass


class T(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.start()

    def run(self):
        while 1:
            print(ts)
            sleep(1)


if __name__ == '__main__':
    ts = 0
    tmax = 10
    T()
    urls = parse_urls('popular_raw.html')
    for path in urls:
        while ts > tmax:
            pass
        P(path)

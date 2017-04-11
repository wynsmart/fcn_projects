import random
import re
import subprocess
import unittest

import utils


def call(cmd, output=False):
    fn = subprocess.check_output if output else subprocess.check_call
    return fn(cmd, shell=True)


class MyTest(unittest.TestCase):
    def setUp(self):
        self.port = random.randint(40001, 40030)
        call('./deployCDN -dt -p {}'.format(self.port))
        call('./runCDN -dt -p {}'.format(self.port))

    def get(self, path):
        cmd = 'dig @{} -p {} {}'.format(
            utils.DNS_HOST,
            self.port,
            utils.DNS_NAME, )
        res = call(cmd, output=True)
        x = res.decode().split('\n')
        ip = x[x.index(';; ANSWER SECTION:') + 1].split()[-1]
        call('time wget -O- http://{}:{}/{}'.format(ip, self.port, path))

    def test(self):
        urls = list(self.parse_urls('popular_raw.html'))
        for i in range(1000):
            url = random.choice(urls)
            self.get(url)

    def tearDown(self):
        call('./stopCDN -dt')

    def parse_urls(self, fname):
        with open(fname, encoding='utf8') as f:
            html = f.read()

        for i in range(2000):
            m = re.search(r'a href="([^"]+)', html, re.M)
            html = html[m.end(1):]
            path = m.group(1)
            m = re.search(r'td align="right">([0-9,]+)', html, re.M)
            html = html[m.end(1):]
            visits = int(m.group(1).replace(',', ''))
            print(visits, path)
            yield path


if __name__ == '__main__':
    unittest.main()

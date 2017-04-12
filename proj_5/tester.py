import random
import subprocess
import unittest

import utils
from pre_cache import parse_urls


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
        call('time wget -O- "http://{}:{}/{}"'.format(ip, self.port, path))

    def test(self):
        urls = list(parse_urls('popular_raw.html'))
        for i in range(100):
            url = random.choice(urls)
            self.get(url)

    def tearDown(self):
        call('./stopCDN -dt')


if __name__ == '__main__':
    unittest.main()

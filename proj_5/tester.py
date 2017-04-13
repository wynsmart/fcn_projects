import random
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
        print(cmd)
        res = call(cmd, output=True)
        print(res)
        x = res.decode().split('\n')
        ip = x[x.index(';; ANSWER SECTION:') + 1].split()[-1]
        cmd = 'time wget -O- "http://{}:{}/{}"'.format(ip, self.port, path)
        print(cmd)
        call(cmd)

    def test(self):
        urls = utils.import_paths()
        for i in range(100):
            url = random.choice(urls)
            self.get(url)

    def tearDown(self):
        call('./stopCDN -dt')


if __name__ == '__main__':
    unittest.main()

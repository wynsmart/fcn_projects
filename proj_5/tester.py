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
        self.port = int(input('port: '))
        call('touch a b')
        # call('./deployCDN -dt -p {}'.format(self.port))
        # call('./runCDN -dt -p {}'.format(self.port))

    def tearDown(self):
        # call('./stopCDN -dt')
        call('rm a b')
        pass

    def get(self, path):
        cmd = 'dig @{} -p {} {}'.format(
            utils.DNS_HOST,
            self.port,
            utils.DNS_NAME, )
        print(cmd)
        res = call(cmd, output=True).decode()
        # print(res)
        x = res.split('\n')
        ip = x[x.index(';; ANSWER SECTION:') + 1].split()[-1]

        options = '--quiet --max-redirect=0'
        cmd = 'time wget {} -O a "http://{}:{}{}"'.format(
            options,
            ip,
            self.port,
            path, )
        print(cmd)
        time_a = subprocess.getoutput(cmd).split('\n')
        print(time_a[1])
        cmd = 'time wget {} -O b "http://{}:{}{}"'.format(
            options,
            utils.CDN_ORIGIN_HOST,
            utils.CND_ORIGIN_PORT,
            path, )
        print(cmd)
        time_b = subprocess.getoutput(cmd).split('\n')
        print(time_b[1])
        # assert(time_a < time_b)

        pattern = r'(This page has been accessed \d+ times.)|(<!--.+?-->)'
        with open('a', encoding='utf8') as f:
            a = f.read()
            a = re.sub(pattern, "", a, flags=re.S)
        with open('b', encoding='utf8') as f:
            b = f.read()
            b = re.sub(pattern, "", b, flags=re.S)
        print('<{} {}>'.format(len(a), len(b)))
        self.assertEqual(a, b)

    def test(self):
        urls = utils.import_paths()
        for i in range(20):
            choice = random.randint(0, 2000)
            url = urls[choice]
            print('{:*^80}'.format(choice))
            self.get(url)


if __name__ == '__main__':
    unittest.main()

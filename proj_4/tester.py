from __future__ import print_function
import subprocess
from urlparse import urlparse
import os
import shutil
import time

PASS = '\033[92m'
FAIL = '\033[91m'
ENDC = '\033[0m'

# urls used for testing
urls = [
    # 'http://www.ccs.neu.edu',  # 301
    # 'http://cs5700sp17.ccs.neu.edu/accounts/login/',
    'http://david.choffnes.com/classes/cs4700fa16/project4.php',
]


def test_url(url):
    filename = urlparse(url).path.split('/')[-1] or 'index.html'

    # download with rawhttpget
    try:
        subprocess.check_call(['./rawhttpget', url])
        os.renames(filename, 'tmp/{}'.format(filename))
    except Exception as e:
        print(e)

    # download with curl
    try:
        subprocess.check_call(
            ['curl {} > tmp/_{}'.format(url, filename)], shell=True)
    except Exception as e:
        print(e)

    # check correctness
    code = subprocess.call(
        ['diff', 'tmp/_{}'.format(filename), 'tmp/{}'.format(filename)])
    if code != 0:
        exit('{}Test Case Failed{}'.format(FAIL, ENDC))

    print('=' * 12)


def main():
    # clear out the tmp directory
    shutil.rmtree('tmp', ignore_errors=True)
    os.makedirs('tmp')

    for url in urls:
        print(url)
        test_url(url)

    print('{}All Tests Passed{}'.format(PASS, ENDC))


if __name__ == '__main__':
    while 1:
        main()
        print('\nre-run tests in 2 seconds...\n')
        time.sleep(2)

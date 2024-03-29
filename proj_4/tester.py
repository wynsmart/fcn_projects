from __future__ import print_function
import subprocess
from urlparse import urlparse
import os
import shutil

PASS = '\033[92m'
FAIL = '\033[91m'
ENDC = '\033[0m'

# urls used for testing
urls = [
    # 'http://www.ccs.neu.edu',  # 301
    'http://david.choffnes.com/classes/cs4700fa16/project4.php',
    'http://david.choffnes.com/classes/cs4700sp17/2MB.log',
    'http://david.choffnes.com/classes/cs4700sp17/10MB.log',
    'http://david.choffnes.com/classes/cs4700sp17/50MB.log',
]


def test_url(url):
    filename = urlparse(url).path.split('/')[-1] or 'index.html'

    # download with rawhttpget
    print('>> downloading with rawhttpget')
    try:
        subprocess.check_call(['./rawhttpget', url])
        os.renames(filename, 'tmp/{}'.format(filename))
    except Exception as e:
        exit('{}{}{}'.format(FAIL, e, ENDC))

    # download with curl
    print('>> downloading with curl')
    try:
        subprocess.check_call(
            ['curl {} > tmp/_{}'.format(url, filename)], shell=True)
    except Exception as e:
        exit('{}{}{}'.format(FAIL, e, ENDC))

    # check correctness
    code = subprocess.call(
        ['diff', 'tmp/_{}'.format(filename), 'tmp/{}'.format(filename)])
    if code != 0:
        exit('{}Test Case Failed{}'.format(FAIL, ENDC))

    print('{}[PASSED]{}'.format(PASS, ENDC))
    print('=' * 80)


def main():
    # clear out the tmp directory
    shutil.rmtree('tmp', ignore_errors=True)
    os.makedirs('tmp')

    for url in urls:
        print(url)
        test_url(url)

    print('{}[ALL TESTS PASSED]{}'.format(PASS, ENDC))


if __name__ == '__main__':
    main()

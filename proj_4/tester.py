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
    'http://cs5700sp17.ccs.neu.edu/accounts/login/',
    # 'http://david.choffnes.com/classes/cs4700fa16/project4.php',
]
for url in urls:
    print(url)
    filename = urlparse(url).path.split('/')[-1] or 'index.html'

    # clear out the tmp directory
    shutil.rmtree('tmp', ignore_errors=True)
    os.makedirs('tmp')

    # download with curl
    try:
        subprocess.check_call(
            ['curl {} > tmp/_{}'.format(url, filename)], shell=True)
    except Exception as e:
        print(e)

    # download with rawhttpget
    try:
        subprocess.check_call(['./rawhttpget', url])
    except Exception as e:
        print(e)

    # check correctness
    code = subprocess.call(
        ['diff', 'tmp/_{}'.format(filename), 'tmp/{}'.format(filename)])
    if code != 0:
        exit('{}Test Case Failed{}'.format(FAIL, ENDC))

    print('=' * 12)

print('{}All Tests Passed{}'.format(PASS, ENDC))

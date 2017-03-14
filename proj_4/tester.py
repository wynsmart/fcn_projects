import subprocess
from urlparse import urlparse
import os
import shutil

# urls used for testing
urls = [
    'http://www.ccs.neu.edu',
    'http://david.choffnes.com/classes/cs4700fa16/project4.php',
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
    try:
        subprocess.check_output(
            ['diff', 'tmp/_{}'.format(filename), 'tmp/{}'.format(filename)])
    except Exception as e:
        exit(e)

    print()

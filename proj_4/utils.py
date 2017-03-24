from __future__ import print_function
from struct import pack, unpack
import argparse
import time

args = None


class Timer:
    def __init__(self, duration):
        self.duration = duration
        self.st_time = self.now()

    def timeout(self):
        return (self.now() - self.st_time) >= self.duration

    def now(self):
        return time.time()


def load_args():
    '''Parse the arguments with argparse utility
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('url')

    global args
    args = parser.parse_args()


def log(*arguments):
    '''Logger in debugging mode
    if option '-d' or '--debug' is given
    import debugging outputs will be printed
    '''
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    if args.debug:
        print('{}[dbg]{}'.format(WARNING, ENDC), *arguments)


def calc_checksum(msg):
    if len(msg) & 1:
        msg += pack('!B', 0)

    checksum = 0
    for i in xrange(1, len(msg), 2):
        checksum += unpack('!H', msg[i - 1:i + 1])[0]

    checksum = (checksum >> 16) + (checksum & 0xFFFF)
    checksum += checksum >> 16
    checksum = ~checksum & 0xFFFF
    return checksum

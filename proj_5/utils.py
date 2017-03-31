from __future__ import print_function
from struct import pack, unpack
import argparse
import time

args = None
IFNAME = 'eth0'


class Timer:
    '''Custom timer for some duration, used for timeout controls
    '''
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
    '''Checksum algorithm for given msg, used for TCP/IP checksums
    '''
    if len(msg) & 1:
        msg += pack('!B', 0)

    checksum = 0
    for i in xrange(1, len(msg), 2):
        checksum += unpack('!H', msg[i - 1:i + 1])[0]

    checksum = (checksum >> 16) + (checksum & 0xFFFF)
    checksum += checksum >> 16
    checksum = ~checksum & 0xFFFF
    return checksum


def hexrepr(msg):
    '''Returns the hex representation of given message
    '''
    return ' '.join('{:02x}'.format(ord(x)) for x in msg)


def hexprint(msg):
    '''Prints Wireshark like hex representation of given msg
    '''
    for i in xrange(0, len(msg), 16):
        print('{}   {}'.format(
            hexrepr(msg[i:i + 8]),
            hexrepr(msg[i + 8:i + 16]), ))

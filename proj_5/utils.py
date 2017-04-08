import argparse

args = None


def load_args():
    '''Parse the arguments with argparse utility
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-t', '--test', action='store_true')
    parser.add_argument('-p', '--port', type=int, default=0)
    parser.add_argument('-n', '--name')
    parser.add_argument('-o', '--origin')

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


def hexrepr(msg):
    '''Returns the hex representation of given message
    '''
    return ' '.join('{:02x}'.format(x) for x in msg)


def hexprint(msg):
    '''Prints Wireshark like hex representation of given msg
    '''
    for i in range(0, len(msg), 16):
        print('{}   {}'.format(
            hexrepr(msg[i:i + 8]),
            hexrepr(msg[i + 8:i + 16]), ))

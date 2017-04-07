import argparse

args = None

HTTP_REASON_PHRASES = {
    100: 'Continue',
    101: 'Switching Protocols',
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Time-out',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Large',
    415: 'Unsupported Media Type',
    416: 'Requested range not satisfiable',
    417: 'Expectation Failed',
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Time-out',
    505: 'HTTP Version not supported',
}


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

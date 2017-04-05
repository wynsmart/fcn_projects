import argparse

args = None


def load_args():
    '''Parse the arguments with argparse utility
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-t', '--test', action='store_true')
    parser.add_argument('-p', '--port')
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

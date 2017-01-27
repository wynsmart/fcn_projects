import utils
from conns import MyPaw

# ./webcrawler [username] [password]


def main():
    # An example of using paw.fetch() to get contents of a relative path
    # Note that the host is default by design
    paw = MyPaw(utils.args.username, utils.args.password)
    utils.log(paw.fetch('/fakebook/'))


# ==============================================================================

if __name__ == '__main__':
    utils.load_args()
    utils.log(utils.args)
    main()

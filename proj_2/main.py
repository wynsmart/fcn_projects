import utils
from conns import MyPaw

# ./webcrawler [username] [password]


def main():
    # An example of using paw.fetch() to get contents of a relative path
    # Note that the host is default by design
    paw = MyPaw(utils.args.username, utils.args.password)
    utils.log(paw.fetch('/fakebook/'))

    # You may implement a class called MyCrawler, then paw can be a property of
    # the instances. Like this
    # class MyCrawler:
    #     def __init__(self):
    #         self.fetch = MyPaw(username, password).fetch


# ==============================================================================

if __name__ == '__main__':
    utils.load_args()
    utils.log(utils.args)
    main()

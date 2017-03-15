from __future__ import print_function
import utils
from conns import MyHTTP

# ./rawhttpget [url]


def main():
    http = MyHTTP()
    http.get(utils.args.url)


if __name__ == '__main__':
    utils.load_args()
    utils.log(utils.args.url)
    main()

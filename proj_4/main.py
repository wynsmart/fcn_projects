from __future__ import print_function
import utils
from myhttp import MyHTTP

# ./rawhttpget [url]

if __name__ == '__main__':
    utils.load_args()
    utils.log(utils.args.url)
    MyHTTP().get(utils.args.url)

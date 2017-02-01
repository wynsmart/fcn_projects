import utils
from crawler import MyCrawler

# ./webcrawler [username] [password]
# initialize MyCrawler which calls MyPaw which creates MyHTTP wrapper
if __name__ == '__main__':
    utils.load_args()
    utils.log(utils.args)
    MyCrawler(utils.args.username, utils.args.password).crawl(
        '/fakebook/', maxthreads=utils.args.threads)

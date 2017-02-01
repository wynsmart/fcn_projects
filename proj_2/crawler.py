import re
import threading
from utils import log
from conns import MyPaw


# crawler class implementing Breadth-First Search given a root URL
class MyCrawler:
    def __init__(self, username, password):
        self.fetch = MyPaw(username, password).fetch
        self.secret_pattern = (r'<h2 class=\'secret_flag\' style="color:red">'
                               + r'FLAG: (.{64})' + r'</h2>')
        self.secrets = []
        self.threads = 0

    # methood to parse the HTML source and use a regex to get all
    # URL tags and their content
    def parseLinks(self, res):
        hrefs = re.findall(r'<a href=\"\/[^\"]+\"', res)
        links = [l[9:-1] for l in hrefs]
        return links

    # crawl method implementing BFS with threads
    def crawl(self, root, maxthreads=10):
        def worker():
            path = q.pop(0)
            log('unique: {} queued: {} threads: {} node: {}'.format(
                len(seen), len(q), self.threads, path))
            res = self.fetch(path)
            sec_match = re.search(self.secret_pattern, res)
            if sec_match:
                secret = sec_match.group(1)
                self.secrets.append(secret)
                print(secret)
            for l in self.parseLinks(res):
                if l not in seen:
                    seen.add(l)
                    q.append(l)
            self.threads -= 1

        q = [root]
        seen = set(q)

        # initialize a threads to speed up crawling
        # end execution on obtaining 5 flags
        while (q or self.threads) and (len(self.secrets) < 5):
            if q and self.threads < maxthreads:
                self.threads += 1
                t = threading.Thread(target=worker)
                t.start()
            # log('unique: {} queued: {} threads: {}'.format(
            #     len(seen), len(q), self.threads))

        log(self.secrets)

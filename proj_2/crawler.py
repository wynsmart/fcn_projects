import re
import threading
from utils import log
from conns import MyPaw


class MyCrawler:
    def __init__(self, username, password):
        self.fetch = MyPaw(username, password).fetch
        self.secret_pattern = (r'<h2 class=\'secret_flag\' style="color:red">'
                               + r'FLAG: (.{64})' + r'</h2>')
        self.secrets = []

    def parseLinks(self, res):
        hrefs = re.findall(r'<a href=\"\/[^\"]+\"', res)
        links = [l[9:-1] for l in hrefs]
        return links

    def crawl(self, root, maxthreads=10):
        def worker():
            path = q.pop(0)
            log('unique: {} queued: {} threads: {} node: {}'.format(
                len(seen), len(q), len(threads), path))
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

        q = [root]
        threads = []
        seen = set(q)
        while (q or threads) and (len(self.secrets) < 5):
            if q and len(threads) < maxthreads:
                t = threading.Thread(target=worker)
                threads.append(t)
                t.start()
            threads = [t for t in threads if t.is_alive()]
            # log('unique: {} queued: {} threads: {}'.format(
            #     len(seen), len(q), len(threads)))

        log(self.secrets)

import re
from utils import log
from conns import MyPaw


class MyCrawler:
    def __init__(self, username, password):
        self.fetch = MyPaw(username, password).fetch
        self.secrets = []

    def parseLinks(self, res):
        hrefs = re.findall(r'<a href=\"\/[^\"]+\"', res)
        links = [l[9:-1] for l in hrefs]
        return links

    def crawl(self, root):
        q = [root]
        color = {}
        while q:
            path = q.pop(0)
            res = self.fetch(path)
            links = self.parseLinks(res)
            color[path] = 2
            log('discovered:', len(color))
            sec_pat = r'<h2 class=\'secret_flag\' style="color:red">FLAG: (.{64})</h2>'
            sec_match = re.search(sec_pat, res)
            if sec_match:
                secret = sec_match.group(1)
                self.secrets.append(secret)
            for l in links:
                if l not in color:
                    color[l] = 1
                    q.append(l)

        for secret in self.secrets:
            print(secret)

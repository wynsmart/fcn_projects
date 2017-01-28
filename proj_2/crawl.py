#! /usr/bin/env python
from conns import MyPaw

class CrawlCrawl(object):
    def __init__(self):
        self.fetch = MyPaw('malgorythmic','password').fetch()
        self.flags = 0
        self.visited = {}
        self.unvisited = []

    def crawl(self, url):

      # <a href=".+">(.*?)<\/a>
      # <h2 class='secret_flag' style="color:red">(.*?)<\/h2>

      while self.unvisited is not None:
        # HTTP GET

        traverse_url = self.unvisited[0]
        self.unvisited.remove(traverse_url)
        self.visited[traverse_url] = True

        # data = HTTP GET traverse_url
        # parse data into a string
        # regex to get list of URLS
        for url_a in regex_result:
            if url_a in self.visited:
                continue
            else:
                self.unvisited.append(url_a)
        # regex to get <h2 class="secret_flag"> tags & get flag and print

        if self.flags == 5:
            break

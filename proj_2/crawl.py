#! /usr/bin/env python

_visited = {}
_unvisited = []
_cookie = ""
_flagcount = 0

def crawl(url):
  global _visited
  global _unvisited

  # <a href=".+">(.*?)<\/a>
  # <h2 class='secret_flag' style="color:red">(.*?)<\/h2>

  while _unvisited is not None:
    # HTTP GET
    traverse_url = _unvisited[0]
    _unvisited.remove(traverse_url)
    _visited[url] = True
    # data = HTTP GET traverse_url
    # parse data into a string
    # regex to get list of URLS
    for url_a in regex_result:
        if url_a in _visited:
            continue
        else:
            unvisited.append(url_a)
    # regex to get <h2 class="secret_flag"> tags & get flag and print

    if _flagcount == 5:
        break

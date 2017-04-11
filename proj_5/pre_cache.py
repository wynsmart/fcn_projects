import re
import subprocess


def parse_urls(fname):
    with open(fname, encoding='utf8') as f:
        html = f.read()

    for i in range(2000):
        m = re.search(r'a href="([^"]+)', html, re.M)
        html = html[m.end(1):]
        path = m.group(1)
        m = re.search(r'td align="right">([0-9,]+)', html, re.M)
        html = html[m.end(1):]
        visits = int(m.group(1).replace(',', ''))
        print(visits, path)
        yield path


urls = parse_urls('popular_raw.html')
for path in urls:
    subprocess.call('wget -O- http://localhost:55555/{}'.format(path), shell=True)

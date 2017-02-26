import re


class Packet:
    '''Packet parser for trace file
    Full reference is available at
    http://www.isi.edu/nsnam/ns/doc/node622.html
    '''
    def __init__(self, raw):
        self.raw = raw

        m = re.findall(r'-[a-z] (\{.+\}|\S+)', self.raw)
        self.event = self.raw[0]
        self.time = float(m[0])
        self.src = int(m[1])
        self.dest = int(m[2])
        self.type = m[3]
        self.size = int(m[4])
        self.conv = int(m[5])
        self.id = int(m[6])

        x_m = re.match(r'\{(\S+) (\S+) (\S+).+\}', m[8])
        self.x_src = x_m.group(1)
        self.x_dest = x_m.group(2)
        self.x_seq = x_m.group(3)

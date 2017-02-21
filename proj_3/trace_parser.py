import re
import matplotlib.pyplot as plt

# throughput = sum(received_size) / total_time     (for each cbr rate)
# latency = end_time - start_time   (for each package)
# drops = total_received_packages - total_sent_packages    (for each flow)


class Packet:
    def __init__(self, raw):
        self.raw = raw
        self.parse()

    def parse(self):
        m = re.match(
            r'^{0} -t {0} -s {0} -d {0} -p {0} -e {0} -c {0} -i {0} .*$'.
            format('(\S+)'), self.raw)
        self.event = m.group(1)
        self.time = float(m.group(2))
        self.src = int(m.group(3))
        self.dest = int(m.group(4))
        self.type = m.group(5)
        self.size = int(m.group(6))
        self.conv = int(m.group(7))
        self.id = int(m.group(8))


class Analyzer:
    def __init__(self, packets):
        self.packets = packets
        self.tcps = [p for p in packets if p.type == 'tcp']
        self.cbrs = [p for p in packets if p.type == 'cbr']

    def calc_throughput(self, st, ed):
        throughput = sum([
            p.size / 1000 for p in self.tcps
            if p.event == 'r' and p.dest == 3 and (st <= p.time < ed)
        ]) / (ed - st)
        return throughput


def main():
    for tcp in ['Tahoe', 'Reno', 'NewReno', 'Vegas']:
        print('# {} ######'.format(tcp))
        for bw in range(1, 11):
            file_path = 'proj_3/Exp_1_Basic/logs/{}_{}.log'.format(tcp, bw)
            with open(file_path) as f:
                events = f.readlines()
            packets = [Packet(e) for e in events if e[0] in 'hrd+-']
            analyzer = Analyzer(packets)
            y = analyzer.calc_throughput(10, 20)
            print(y)


if __name__ == '__main__':
    main()

import re
# import matplotlib.pyplot as plt

# throughput = sum(received_size) / total_time     (for each cbr rate)
# latency = end_time - start_time   (for each package)
# drops = total_received_packages - total_sent_packages    (for each flow)

# +
# time: -t 0.1
# src: -s 0
# dest: -d 1
# package type: -p tcp
# size(bytes): -e 40
# conv: -c 1
# id: -i 0
# attributes: -a 1
# -x {0.0 3.0 0 ------- null}

dir_base = 'proj_3/Exp_1_Basic/'


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

    def calc_throughputs(self, time_steps):
        throughput = []
        for i in range(1, len(time_steps)):
            st = time_steps[i - 1]
            ed = time_steps[i]
            throughput.append(
                sum([
                    p.size / 1000 for p in self.tcps
                    if p.event == 'r' and p.dest == 2 and (st <= p.time < ed)
                ]) / (ed - st))
        return throughput

    # def plot(self, x, y):
    #     plt.plot(x, y, 'o-')
    #     plt.grid(True)
    #     plt.xticks(x)
    #     plt.yticks(range(0, 500, 100))
    #     # plt.savefig(dir_base + 'filename.jpg')
    #     plt.show()


def main():
    # file_path = dir_base + 'exp_one_tahoe.nam'
    file_path = '/Users/iSMart/Desktop/test_10s.nam'
    with open(file_path) as f:
        events = f.readlines()
    packets = [Packet(e) for e in events if e[0] in 'hrd+-']
    analyzer = Analyzer(packets)
    x = range(1, 11)
    y = analyzer.calc_throughputs(
        range(10, 111, 10))
    print(y)


if __name__ == '__main__':
    main()

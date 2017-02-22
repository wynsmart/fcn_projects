import re
import sys

# throughput = sum(received_size) / time
# latency = end_time - start_time
# droprate = (sent_packets - received_packets) / sent_packets


class Packet:
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


class Analyzer:
    def __init__(self, events):
        self.st = 10
        self.ed = 15
        packets = [Packet(e) for e in events if e[0] in 'r+']
        self.packets = [p for p in packets if self.st <= p.time < self.ed]

    def calc_throughput(self, x_dest):
        # unit in Mbit/s
        dest = int(float(x_dest))
        throughput = sum([
            p.size * 8 / 1000000 for p in self.packets
            if p.event == 'r' and p.dest == dest and p.x_dest == x_dest
        ]) / (self.ed - self.st)
        return '{:.3f}'.format(throughput)

    def calc_latency(self, x_src):
        # unit in ms
        src = int(float(x_src))
        tcps = {
            p.x_seq: p
            for p in self.packets
            if p.type == 'tcp' and p.event == '+' and p.src == src and p.x_src
            == x_src
        }
        acks = {
            p.x_seq: p
            for p in self.packets
            if p.type == 'ack' and p.event == 'r' and p.dest == src and
            p.x_dest == x_src
        }
        latencies = [
            acks[seq].time - tcps[seq].time for seq in acks if seq in tcps
        ]
        if not latencies:
            return ''
        avg_latency = sum(latencies) / len(latencies) * 1000
        return '{:.2f}'.format(avg_latency)

    def calc_droprate(self, x_src):
        # unit in cents
        src = int(float(x_src))
        sents = len([
            1 for p in self.packets
            if p.type == 'tcp' and p.event == '+' and p.src == src and p.x_src
            == x_src
        ])
        recvs = len([
            1 for p in self.packets
            if p.type == 'ack' and p.event == 'r' and p.dest == src and
            p.x_dest == x_src
        ])
        if recvs == 0:
            return ''
        droprate = (sents - recvs) / sents * 100
        return '{:.2f}'.format(droprate)


def exp3_1():
    with open('data-1.csv', mode='w') as data_f:
        tcpTypes = ['Reno', 'Sack']
        header = ','.join(['BW'] + tcpTypes * 2)
        print(header)
        data_f.write('{}\n'.format(header))
        for bw in range(1, 11):
            throughputs = []
            latencies = []
            droprates = []
            log_dir = 'logs/scenario-2/'
            log_file = log_dir + '{}.log'.format(bw)
            with open(log_file) as logf:
                events = logf.readlines()
            analyzer = Analyzer(events)
            for i in range(4):
                throughputs.append(analyzer.calc_throughput('3.{}'.format(i)))
                latencies.append(analyzer.calc_latency('0.{}'.format(i)))
                droprates.append(analyzer.calc_droprate('0.{}'.format(i)))
            line = ','.join([str(bw)] + throughputs + latencies + droprates)
            print(line)
            data_f.write('{}\n'.format(line))


if __name__ == '__main__':
    exp = [None, exp3_1]
    scenario = int(sys.argv[1])
    exp[scenario]()

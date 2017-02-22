import re

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

    def calc_throughput(self, dest):
        # unit in Mbit/s
        throughput = sum([
            p.size * 8 / 1000000 for p in self.packets
            if p.event == 'r' and p.dest == dest
        ]) / (self.ed - self.st)
        return '{:.3f}'.format(throughput)

    def calc_latency(self, src):
        # unit in ms
        tcps = {
            p.x_seq: p
            for p in self.packets
            if p.type == 'tcp' and p.event == '+' and p.src == src
        }
        acks = {
            p.x_seq: p
            for p in self.packets
            if p.type == 'ack' and p.event == 'r' and p.dest == src
        }
        latencies = [
            acks[seq].time - tcps[seq].time for seq in acks if seq in tcps
        ]
        if not latencies:
            return ''
        avg_latency = sum(latencies) / len(latencies) * 1000
        return '{:.2f}'.format(avg_latency)

    def calc_droprate(self, src):
        # unit in cents
        sents = len([
            1 for p in self.packets
            if p.type == 'tcp' and p.event == '+' and p.src == src
        ])
        recvs = len([
            1 for p in self.packets
            if p.type == 'ack' and p.event == 'r' and p.dest == src
        ])
        if recvs == 0:
            return ''
        droprate = (sents - recvs) / sents * 100
        return '{:.2f}'.format(droprate)


def exp2_1():
    tcpPairs = [
        ('Reno', 'Reno'),
        ('NewReno', 'Reno'),
        ('Vegas', 'Vegas'),
        ('NewReno', 'Vegas'),
    ]
    for tcp1, tcp2 in tcpPairs:
        with open('data-1-{}-{}.csv'.format(tcp1, tcp2), mode='w') as data_f:
            header = ','.join(['BW'] + [tcp1, tcp2] * 3)
            print(header)
            data_f.write('{}\n'.format(header))
            for bw in range(1, 11):
                throughputs = []
                latencies = []
                droprates = []
                log_dir = 'logs/scenario-1/'
                log_file = log_dir + '{}_{}_{}.log'.format(tcp1, tcp2, bw)
                with open(log_file) as logf:
                    events = logf.readlines()
                analyzer = Analyzer(events)
                throughputs.append(analyzer.calc_throughput(3))
                latencies.append(analyzer.calc_latency(0))
                droprates.append(analyzer.calc_droprate(0))
                throughputs.append(analyzer.calc_throughput(5))
                latencies.append(analyzer.calc_latency(4))
                droprates.append(analyzer.calc_droprate(4))
                line = ','.join([str(bw)] + throughputs + latencies +
                                droprates)
                print(line)
                data_f.write('{}\n'.format(line))


if __name__ == '__main__':
    exp2_1()

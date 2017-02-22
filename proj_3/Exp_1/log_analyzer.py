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

    def calc_throughput(self):
        # unit in Mbit/s
        throughput = sum([
            p.size * 8 / 1000000 for p in self.packets
            if p.event == 'r' and p.dest == 3
        ]) / (self.ed - self.st)
        return '{:.3f}'.format(throughput)

    def calc_latency(self):
        # unit in ms
        tcps = {
            p.x_seq: p
            for p in self.packets
            if p.type == 'tcp' and p.event == '+' and p.src == 0
        }
        acks = {
            p.x_seq: p
            for p in self.packets
            if p.type == 'ack' and p.event == 'r' and p.dest == 0
        }
        latencies = [
            acks[seq].time - tcps[seq].time for seq in acks if seq in tcps
        ]
        if not latencies:
            return ''
        avg_latency = sum(latencies) / len(latencies) * 1000
        return '{:.2f}'.format(avg_latency)

    def calc_droprate(self):
        # unit in cents
        sents = len([
            1 for p in self.packets
            if p.type == 'tcp' and p.event == '+' and p.src == 0
        ])
        recvs = len([
            1 for p in self.packets
            if p.type == 'ack' and p.event == 'r' and p.dest == 0
        ])
        if recvs == 0:
            return ''
        droprate = (sents - recvs) / sents * 100
        return '{:.2f}'.format(droprate)


def exp1(scenario):
    tcpTypes = ['Tahoe', 'Reno', 'NewReno', 'Vegas']
    with open('data-{}.csv'.format(scenario), mode='w') as data_f:
        header = ','.join(['BW'] + tcpTypes * 3)
        print(header)
        data_f.write('{}\n'.format(header))
        for bw in range(1, 11):
            throughputs = []
            latencies = []
            droprates = []
            for tcp in tcpTypes:
                log_dir = 'logs/scenario-{}/'.format(scenario)
                log_file = log_dir + '{}_{}.log'.format(tcp, bw)
                with open(log_file) as logf:
                    events = logf.readlines()
                analyzer = Analyzer(events)
                throughputs.append(analyzer.calc_throughput())
                latencies.append(analyzer.calc_latency())
                droprates.append(analyzer.calc_droprate())
            line = ','.join([str(bw)] + throughputs + latencies + droprates)
            print(line)
            data_f.write('{}\n'.format(line))


if __name__ == '__main__':
    scenario = int(sys.argv[1])
    exp1(scenario)

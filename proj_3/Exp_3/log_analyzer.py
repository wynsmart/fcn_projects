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
        self.t_st = 0
        self.t_ed = 30
        packets = [Packet(e) for e in events if e[0] in 'r+']
        self.t_packets = {t: [] for t in range(self.t_st, self.t_ed)}
        for p in packets:
            t = int(p.time)
            self.t_packets[t].append(p)

    def calc_throughput(self, t, x_dest):
        # unit in Mbit/s
        dest = int(float(x_dest))
        throughput = sum([
            p.size for p in self.t_packets[t]
            if p.event == 'r' and p.dest == dest and p.x_dest == x_dest
        ]) * 8 / 1000000
        return '{:.3f}'.format(throughput)

    def calc_latency(self, t, x_src):
        # unit in ms
        src = int(float(x_src))
        tcps = {
            p.x_seq: p
            for p in self.t_packets[t]
            if p.type == 'tcp' and p.event == '+' and p.src == src and p.x_src
            == x_src
        }
        acks = {
            p.x_seq: p
            for p in self.t_packets[t]
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


def exp3_1():
    cbr_bw = 8
    with open('data-1.csv', mode='w') as data_f:
        tcpTypes = ['Reno', 'Sack']
        queueAlgos = ['DropTail', 'RED']
        pairs = []
        analyzers = []
        for q in queueAlgos:
            for tcp in tcpTypes:
                log_dir = 'logs/scenario-1/'
                log_file = log_dir + '{}_{}_{}.log'.format(q, tcp, cbr_bw)
                with open(log_file) as logf:
                    events = logf.readlines()
                pair = '{}/{}'.format(q, tcp)
                pairs.append(pair)
                analyzers.append(Analyzer(events))
        header = ','.join(['Time'] + pairs * 2)
        print(header)
        data_f.write('{}\n'.format(header))
        for t in range(30):
            throughputs = []
            latencies = []
            for analyzer in analyzers:
                throughputs.append(analyzer.calc_throughput(t, '3.0'))
                latencies.append(analyzer.calc_latency(t, '0.0'))
            line = ','.join([str(t)] + throughputs + latencies)
            print(line)
            data_f.write('{}\n'.format(line))


if __name__ == '__main__':
    exp = [None, exp3_1]
    scenario = int(sys.argv[1])
    exp[scenario]()

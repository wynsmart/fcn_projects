import os
import sys
from packet import Packet


class Analyzer:
    def __init__(self, events):
        self.t_st = 0
        self.t_ed = 20
        packets = [Packet(e) for e in events if e[0] in 'r+']
        self.t_packets = {t: [] for t in range(self.t_st, self.t_ed)}
        for p in packets:
            t = int(p.time)
            self.t_packets[t].append(p)

    def calc_throughput(self, t, x_dest):
        '''throughput = sum(received_size) / time
        unit in Mbit/s
        '''
        dest = int(float(x_dest))
        throughput = sum([
            p.size for p in self.t_packets[t]
            if p.event == 'r' and p.dest == dest and p.x_dest == x_dest
        ]) * 8 / 1000000
        return '{:.3f}'.format(throughput)

    def calc_latency(self, t, x_src):
        '''latency = end_time - start_time
        unit in ms
        '''
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


def exp3(scenario):
    '''Analyze scenarios of experiment 3
    refer README for more details on scenario settings
    generates csv files for futher plotting
    '''
    with open('data-{}.csv'.format(scenario), mode='w') as data_f:
        tcpTypes = ['Reno', 'Sack']
        queueAlgos = ['RED', 'DropTail']
        pairs = []
        analyzers = {}
        for q in queueAlgos:
            for tcp in tcpTypes:
                log_dir = 'logs/scenario-{}/'.format(scenario)
                log_file = log_dir + '{}_{}.log'.format(q, tcp)
                with open(log_file) as logf:
                    events = logf.readlines()
                os.remove(log_file)
                pair = '{}/{}'.format(q, tcp)
                pairs.append(pair)
                analyzers[pair] = Analyzer(events)
        header = ','.join(['Time', 'CBR'] + pairs * 2)
        print(header)
        data_f.write('{}\n'.format(header))
        for t in range(20):
            throughputs = []
            latencies = []
            throughputs.append(analyzers[pairs[0]].calc_throughput(t, '5.0'))
            for pair in pairs:
                throughputs.append(analyzers[pair].calc_throughput(t, '3.0'))
                latencies.append(analyzers[pair].calc_latency(t, '0.0'))
            line = ','.join([str(t)] + throughputs + latencies)
            print(line)
            data_f.write('{}\n'.format(line))


if __name__ == '__main__':
    scenario = int(sys.argv[1])
    exp3(scenario)

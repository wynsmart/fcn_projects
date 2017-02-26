import os
import sys
from packet import Packet


class Analyzer:
    def __init__(self, events):
        self.st = 10
        self.ed = 15
        packets = [Packet(e) for e in events if e[0] in 'r+']
        self.packets = [p for p in packets if self.st <= p.time < self.ed]

    def calc_throughput(self):
        '''throughput = sum(received_size) / time
        unit in Mbit/s
        '''
        throughput = sum([
            p.size for p in self.packets if p.event == 'r' and p.dest == 3
        ]) / (self.ed - self.st) * 8 / 1000000
        return '{:.3f}'.format(throughput)

    def calc_latency(self):
        '''latency = end_time - start_time
        unit in ms
        '''
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
        '''droprate = (sent_packets - received_packets) / sent_packets
        unit in cents
        '''
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
    '''Analyze scenarios of experiment 1
    refer README for more details on scenario settings
    generates csv files for futher plotting
    '''
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
                os.remove(log_file)
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

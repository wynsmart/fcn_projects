import os
import sys
from packet import Packet


class Analyzer:
    def __init__(self, events):
        self.st = 10
        self.ed = 15
        packets = [Packet(e) for e in events if e[0] in 'r+']
        self.packets = [p for p in packets if self.st <= p.time < self.ed]

    def calc_throughput(self, x_dest):
        '''throughput = sum(received_size) / time
        unit in Mbit/s
        '''
        dest = int(float(x_dest))
        throughput = sum([
            p.size for p in self.packets
            if p.event == 'r' and p.dest == dest and p.x_dest == x_dest
        ]) / (self.ed - self.st) * 8 / 1000000
        return '{:.3f}'.format(throughput)

    def calc_latency(self, x_src):
        '''latency = end_time - start_time
        unit in ms
        '''
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
        '''droprate = (sent_packets - received_packets) / sent_packets
        unit in cents
        '''
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


def exp2_1():
    '''Analyze scenario 1 of experiment 2
    refer README for more details on scenario settings
    generates csv files for futher plotting
    '''
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
                os.remove(log_file)
                analyzer = Analyzer(events)
                throughputs.append(analyzer.calc_throughput('3.0'))
                latencies.append(analyzer.calc_latency('0.0'))
                droprates.append(analyzer.calc_droprate('0.0'))
                throughputs.append(analyzer.calc_throughput('5.0'))
                latencies.append(analyzer.calc_latency('4.0'))
                droprates.append(analyzer.calc_droprate('4.0'))
                line = ','.join([str(bw)] + throughputs + latencies +
                                droprates)
                print(line)
                data_f.write('{}\n'.format(line))


def exp2_2():
    '''Analyze scenario 2 of experiment 2
    refer README for more details on scenario settings
    generates csv files for futher plotting
    '''
    with open('data-2.csv', mode='w') as data_f:
        tcpTypes = ['Tahoe', 'Reno', 'NewReno', 'Vegas']
        header = ','.join(['BW'] + tcpTypes * 3)
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
            os.remove(log_file)
            analyzer = Analyzer(events)
            for i in range(4):
                throughputs.append(analyzer.calc_throughput('3.{}'.format(i)))
                latencies.append(analyzer.calc_latency('0.{}'.format(i)))
                droprates.append(analyzer.calc_droprate('0.{}'.format(i)))
            line = ','.join([str(bw)] + throughputs + latencies + droprates)
            print(line)
            data_f.write('{}\n'.format(line))


if __name__ == '__main__':
    exp = [None, exp2_1, exp2_2]
    scenario = int(sys.argv[1])
    exp[scenario]()

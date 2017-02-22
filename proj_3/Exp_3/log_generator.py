import subprocess
import os
import sys

tcps = {
    'Reno': 'Agent/TCP/Reno',
    'Sack': 'Agent/TCP/Sack1',
}
queues = {
    'DropTail': 'DropTail',
    'RED': 'RED',
}
bw = 8


def genData_1(tcl_src):
    for q in queues:
        for tcp in tcps:
            print('Scenario: 1, Queue: {} TCP: {}, CBR: {}MB'.format(q, tcp,
                                                                     bw))
            log_dir = 'logs/scenario-1/'
            os.makedirs(log_dir, exist_ok=True)
            log_file = log_dir + '{}_{}_{}.log'.format(q, tcp, bw)
            subprocess.call(
                'ns {} {} {} {} {}'.format(tcl_src, queues[q], tcps[tcp], bw,
                                           log_file),
                shell=True)


if __name__ == '__main__':
    exp = [None, genData_1]
    scenario = int(sys.argv[1])
    exp[scenario]('scenario-{}.tcl'.format(scenario))

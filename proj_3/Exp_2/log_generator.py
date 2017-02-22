import subprocess
import os
import sys

tcps = {
    'Tahoe': 'Agent/TCP',
    'Reno': 'Agent/TCP/Reno',
    'NewReno': 'Agent/TCP/Newreno',
    'Vegas': 'Agent/TCP/Vegas',
}
bandwidths = range(1, 11)


def genData_1(tcl_src):
    for tcp1, tcp2 in [
        ('Reno', 'Reno'),
        ('NewReno', 'Reno'),
        ('Vegas', 'Vegas'),
        ('NewReno', 'Vegas'),
    ]:
        for bw in bandwidths:
            print('Scenario: 1, TCP: {}/{}, CBR: {}MB'.format(tcp1, tcp2, bw))
            log_dir = 'logs/scenario-1/'
            os.makedirs(log_dir, exist_ok=True)
            log_file = log_dir + '{}_{}_{}.log'.format(tcp1, tcp2, bw)
            subprocess.call(
                'ns {} {} {} {} {}'.format(tcl_src, tcps[tcp1], tcps[tcp2], bw,
                                           log_file),
                shell=True)


def genData_2(tcl_src):
    for bw in bandwidths:
        print('Scenario: 2, CBR: {}MB'.format(bw))
        log_dir = 'logs/scenario-2/'
        os.makedirs(log_dir, exist_ok=True)
        log_file = log_dir + '{}.log'.format(bw)
        subprocess.call(
            'ns {} {} {}'.format(tcl_src, bw, log_file), shell=True)


if __name__ == '__main__':
    exp = [None, genData_1, genData_2]
    scenario = int(sys.argv[1])
    exp[scenario]('scenario-{}.tcl'.format(scenario))

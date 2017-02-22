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


def genData(scenario, tcl_src):
    for tcp in tcps:
        for bw in bandwidths:
            print('Scenario: {}, TCP: {}, CBR: {}MB'.format(scenario, tcp, bw))
            log_dir = 'logs/scenario-{}/'.format(scenario)
            os.makedirs(log_dir, exist_ok=True)
            log_file = log_dir + '{}_{}.log'.format(tcp, bw)
            subprocess.call(
                'ns {} {} {} {}'.format(tcl_src, tcps[tcp], bw, log_file),
                shell=True)


if __name__ == '__main__':
    scenario = int(sys.argv[1])
    genData(scenario, 'scenario-{}.tcl'.format(scenario))

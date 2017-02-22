import subprocess
import os

tcps = {
    'Tahoe': 'Agent/TCP',
    'Reno': 'Agent/TCP/Reno',
    'NewReno': 'Agent/TCP/Newreno',
    'Vegas': 'Agent/TCP/Vegas',
}
bandwidths = range(1, 11)


def genData(scenario, tcl_src):
    for tcp1, tcp2 in [
        ('Reno', 'Reno'),
        ('NewReno', 'Reno'),
        ('Vegas', 'Vegas'),
        ('NewReno', 'Vegas'),
    ]:
        for bw in bandwidths:
            print('Scenario: {}, TCP: {}/{}, CBR: {}MB'.format(scenario, tcp1,
                                                               tcp2, bw))
            log_dir = 'logs/scenario-{}/'.format(scenario)
            os.makedirs(log_dir, exist_ok=True)
            log_file = log_dir + '{}_{}_{}.log'.format(tcp1, tcp2, bw)
            subprocess.call(
                'ns {} {} {} {} {}'.format(tcl_src, tcps[tcp1], tcps[tcp2], bw,
                                           log_file),
                shell=True)


genData(1, 'scenario-1.tcl')

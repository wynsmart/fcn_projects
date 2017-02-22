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


def genData(scenario):
    cbr_bws = [None, 6, 8]
    tcl_src = 'scenario-1.tcl'
    for q in queues:
        for tcp in tcps:
            print('Scenario: {}, Queue: {} TCP: {}, CBR: {}MB'.format(
                scenario, q, tcp, cbr_bws[scenario]))
            log_dir = 'logs/scenario-{}/'.format(scenario)
            os.makedirs(log_dir, exist_ok=True)
            log_file = log_dir + '{}_{}.log'.format(q, tcp)
            subprocess.call(
                'ns {} {} {} {} {}'.format(tcl_src, queues[q], tcps[tcp],
                                           cbr_bws[scenario], log_file),
                shell=True)


if __name__ == '__main__':
    scenario = int(sys.argv[1])
    genData(scenario)

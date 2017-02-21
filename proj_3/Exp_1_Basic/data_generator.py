import subprocess

tcps = {
    'Tahoe': 'Agent/TCP',
    'Reno': 'Agent/TCP/Reno',
    'NewReno': 'Agent/TCP/Newreno',
    'Vegas': 'Agent/TCP/Vegas',
}
bandwidths = range(1, 11)


def genData(tcl_src):
    for tcp in tcps:
        for bw in bandwidths:
            trace_file = 'logs/{}_{}.log'.format(tcp, bw)
            subprocess.call(
                'ns {} {} {} {}'.format(tcl_src, tcps[tcp], bw, trace_file),
                shell=True)


genData('experiment_one_basic.tcl')

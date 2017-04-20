import random
import subprocess
import threading

import utils

DNS_FILES = [
    'dnsserver',
    'dnsserver.py',
    'utils.py',
    'Makefile',
]
CDN_FILES = [
    utils.PAGES,
    'httpserver',
    'httpserver.py',
    'utils.py',
    'Makefile',
]


class MyCDN:
    '''implements deploy/run/stop of CDNs and DNS
    '''

    def __init__(self, mode, port, origin, name, username, keyfile):
        self.debug = '-d' if utils.args.debug else ''
        self.port = port
        self.origin = origin
        self.name = name
        self.username = username
        self.keyfile = keyfile
        self.ROOT_DIR = '~/proj_5'
        self.threads = 0
        mode_handler = {
            'deploy': self.deploy,
            'run': self.run,
            'stop': self.stop,
        }
        mode_handler[mode]()

    def wait_sync(self):
        '''wait for all threads completion
        '''
        while self.threads:
            utils.log('waiting {}'.format(self.threads),
                      override=True,
                      force=True)

    def deploy(self):
        '''deploy by copying files to CDNs and DNS
        '''
        utils.log('copying files ...', force=True)
        RemoteWorker(self, self._deploy, [utils.DNS_HOST, DNS_FILES])
        for host in utils.CDN_HOSTS:
            RemoteWorker(self, self._deploy, [host, CDN_FILES])
        self.wait_sync()
        utils.log('deploy finished', force=True)

    def _deploy(self, host, flist):
        '''actually copy essential files to given host
        '''
        # prepare directories on remote
        cmds = ' && '.join([
            'mkdir -p {}'.format(self.ROOT_DIR),
            'rm -rf {}/*'.format(self.ROOT_DIR),
        ])
        self.ssh(host, cmds)
        # copy files to remote
        fname = ' '.join(flist)
        self.scp(host, fname)
        utils.log(host, force=True)

    def run(self):
        '''start CDNs firstly then DNS
        '''
        utils.log('starting ...', force=True)
        for host in utils.CDN_HOSTS:
            RemoteWorker(self, self.run_cdn, [host])
        self.wait_sync()
        RemoteWorker(self, self.run_dns, [utils.DNS_HOST])
        self.wait_sync()
        utils.log('serving on port', self.port, force=True)

    def run_dns(self, host):
        '''actually start given DNS host, with validation
        '''
        cmds = '  && '.join([
            'cd {}'.format(self.ROOT_DIR),
            'make -s dns',
            '(./dnsserver {} -p {} -n {} >log 2>&1 &)'.format(
                self.debug,
                self.port,
                self.name, ),
        ])
        self.ssh(host, cmds)
        self._run_validate(host)

    def run_cdn(self, host):
        '''actually start given CDN host, with validation
        '''
        cmds = ' && '.join([
            'cd {}'.format(self.ROOT_DIR),
            'make -s cdn',
            '(./httpserver {} -p {} -o {} >log 2>&1 &)'.format(
                self.debug,
                self.port,
                self.origin, ),
        ])
        self.ssh(host, cmds)
        self._run_validate(host)

    def _run_validate(self, host):
        '''validate the running host state by checking log
        '''
        cmd = 'cat {}/log'.format(self.ROOT_DIR)
        log = self.ssh(host, cmd, output=True)
        if 'SERVING {}'.format(self.port) in log:
            utils.log(host, force=True)
        else:
            utils.err('failed to start {}'.format(host))

    def stop(self):
        '''stop DNS firstly then CDNs
        '''
        utils.log('stopping ...', force=True)
        RemoteWorker(self, self._stop, [utils.DNS_HOST])
        self.wait_sync()
        for host in utils.CDN_HOSTS:
            RemoteWorker(self, self._stop, [host])
        self.wait_sync()
        utils.log('cdn stopped', force=True)

    def _stop(self, host):
        '''actually stop the given host by killing processes
        '''
        cmd = 'pkill -9 -u $USER python || :'
        self.ssh(host, cmd)
        utils.log(host, force=True)

    def scp(self, host, fname):
        '''transfer given files to remote server
        '''
        cmd = "tar -czf - {} | ssh -C -i {} {}@{} 'cd {} && tar -xzf -'"
        subs = (fname, self.keyfile, self.username, host, self.ROOT_DIR)
        subprocess.check_call(cmd.format(*subs), shell=True)

    def ssh(self, host, cmd, output=False):
        '''execute a command on remote server
        '''
        cmd = "ssh -o StrictHostKeyChecking=no -i {} {}@{} '{}'".format(
            self.keyfile,
            self.username,
            host,
            cmd, )
        if output:
            result = subprocess.check_output(cmd, shell=True, timeout=30)
            return result.decode() if result else ''
        else:
            subprocess.check_call(cmd, shell=True, timeout=30)


class RemoteWorker(threading.Thread):
    '''MultiThread worker for a given function job
    '''

    def __init__(self, caller, fn, args):
        super().__init__()
        self.caller = caller
        self.fn = fn
        self.args = args
        self.daemon = True
        self.start()

    def run(self):
        self.caller.threads += 1
        try:
            self.fn(*self.args)
        except Exception as e:
            utils.err(e)
        finally:
            self.caller.threads -= 1


if __name__ == "__main__":
    utils.load_args()
    mode = utils.args.mode
    port = utils.args.port
    origin = utils.args.origin
    name = utils.args.name
    username = utils.args.username
    keyfile = utils.args.keyfile

    if utils.args.test:
        port = port or random.randint(40001, 40030)
        origin = origin or utils.CDN_ORIGIN_HOST
        name = name or utils.DNS_NAME
        username = username or 'wynsmart'
        keyfile = keyfile or '~/.ssh/fcn_ec2_id_rsa'

    if None in (port, origin, name, username, keyfile):
        exit('not enough parameters, check help with `-h`')

    MyCDN(mode, port, origin, name, username, keyfile)

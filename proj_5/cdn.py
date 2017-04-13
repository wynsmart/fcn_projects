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
    'cache/',
    'httpserver',
    'httpserver.py',
    'utils.py',
    'Makefile',
    utils.PAGES,
]


class MyCDN:
    def __init__(self, mode, port, origin, name, username, keyfile):
        self.port = port
        self.origin = origin
        self.name = name
        self.username = username
        self.keyfile = keyfile
        self.ROOT_DIR = '~/proj_5'
        self.threads = 0
        self.dns_fname = 'deploy-dns.tar.gz'
        self.cdn_fname = 'deploy-cdn.tar.gz'
        mode_handler = {
            'deploy': self.deploy,
            'run': self.run,
            'stop': self.stop,
        }
        mode_handler[mode]()

    def wait_sync(self):
        while self.threads:
            pass

    def deploy(self):
        utils.log('packing files ...')
        self.deploy_pack(DNS_FILES, self.dns_fname)
        self.deploy_pack(CDN_FILES, self.cdn_fname)

        utils.log('copying files ...')
        self.deploy_copy(utils.DNS_HOST, self.dns_fname)
        for host in utils.CDN_HOSTS:
            self.deploy_copy(host, self.cdn_fname)
        self.wait_sync()
        self.deploy_cleanup()

        utils.log('extracting files ...')
        self.deploy_extract(utils.DNS_HOST, self.dns_fname)
        for host in utils.CDN_HOSTS:
            self.deploy_extract(host, self.cdn_fname)
        self.wait_sync()

        utils.log('deploy finished')

    def deploy_pack(self, files, fname):
        '''pack and compress files
        '''
        cmd = 'tar -czf {} {}'.format(fname, ' '.join(files))
        subprocess.check_call(cmd, shell=True)

    def deploy_copy(self, host, fname):
        RemoteWorker(self, self.scp, [host, fname])

    def deploy_cleanup(self):
        cmd = 'rm {} {}'.format(self.dns_fname, self.cdn_fname)
        subprocess.check_call(cmd, shell=True)

    def deploy_extract(self, host, fname):
        cmds = ' && '.join([
            'mkdir -p {}'.format(self.ROOT_DIR),
            'rm -rf {}/*'.format(self.ROOT_DIR),
            'tar -xf {} -C {}'.format(fname, self.ROOT_DIR),
            'rm ~/{}'.format(fname),
        ])
        RemoteWorker(self, self.ssh, [host, cmds], msg=host)

    def run(self):
        utils.log('starting ...')
        for host in utils.CDN_HOSTS:
            self.run_cdn(host)
        self.wait_sync()
        self.run_dns(utils.DNS_HOST)
        self.wait_sync()
        utils.log('serving on port', self.port)

    def run_dns(self, host):
        cmds = '  && '.join([
            'cd {}'.format(self.ROOT_DIR),
            'make -s dns',
            '(./dnsserver -d -p {} -n {} >log 2>&1 &)'.format(
                self.port,
                self.name, ),
        ])
        RemoteWorker(self, self.ssh, [host, cmds], msg=host)

    def run_cdn(self, host):
        cmds = ' && '.join([
            'cd {}'.format(self.ROOT_DIR),
            'make -s cdn',
            '(./httpserver -d -p {} -o {} >log 2>&1 &)'.format(
                self.port,
                self.origin, ),
        ])
        RemoteWorker(self, self.ssh, [host, cmds], msg=host)

    def stop(self):
        utils.log('stopping ...')
        self._stop(utils.DNS_HOST)
        self.wait_sync()
        for host in utils.CDN_HOSTS:
            self._stop(host)
        self.wait_sync()
        utils.log('cdn stopped')

    def _stop(self, host):
        cmd = 'pkill python3.4'
        RemoteWorker(self, self.ssh, [host, cmd], msg=host)

    def scp(self, host, fname):
        cmd = 'scp -rp -i {} {} {}@{}:~'.format(
            self.keyfile,
            fname,
            self.username,
            host, )
        try:
            subprocess.check_call(cmd, shell=True)
        except Exception as e:
            utils.log(e)

    def ssh(self, host, cmd):
        cmd = 'ssh -i {} {}@{} "{}"'.format(
            self.keyfile,
            self.username,
            host,
            cmd,)
        try:
            subprocess.check_call(cmd, shell=True, timeout=30)
        except Exception as e:
            utils.log(e)


class RemoteWorker(threading.Thread):
    def __init__(self, caller, fn, args, msg=None):
        super().__init__()
        self.caller = caller
        self.fn = fn
        self.args = args
        self.msg = msg
        self.daemon = True
        self.start()

    def run(self):
        self.caller.threads += 1
        self.fn(*self.args)
        if self.msg is not None:
            utils.log(self.msg)
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
        origin = origin or 'ec2-54-166-234-74.compute-1.amazonaws.com'
        name = name or 'cs5700cdn.example.com'
        username = username or 'wynsmart'
        keyfile = keyfile or '~/.ssh/fcn_ec2_id_rsa'
    MyCDN(mode, port, origin, name, username, keyfile)

import random
import subprocess
from time import sleep

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
]


class MyCDN:
    def __init__(self, mode, port, origin, name, username, keyfile):
        self.port = port
        self.origin = origin
        self.name = name
        self.username = username
        self.keyfile = keyfile
        self.root = '~/proj_5'
        mode_handler = {
            'deploy': self.deploy,
            'run': self.run,
            'stop': self.stop,
        }
        mode_handler[mode]()

    def deploy(self):
        utils.log('deploying ...')
        self.procs = []
        self.deploy_dns(utils.DNS_HOST)
        for host in utils.CDN_HOSTS:
            self.deploy_cdn(host)

        while len(self.procs):
            self.procs = [p for p in self.procs if p.poll() is None]
            utils.log('remain jobs: {:3}'.format(len(self.procs)),
                      override=True)
            sleep(2)
        utils.log()
        utils.log('finished.')

    def deploy_dns(self, host):
        utils.log('host:', host)
        try:
            self.ssh(host, 'mkdir -p {}'.format(self.root))
            self.ssh(host, 'rm -rf {}/*'.format(self.root))
            self.scp_async(host, DNS_FILES)
        except Exception as e:
            utils.log(e)

    def deploy_cdn(self, host):
        utils.log('host:', host)
        try:
            self.ssh(host, 'mkdir -p {}'.format(self.root))
            self.ssh(host, 'rm -rf {}/*'.format(self.root))
            self.scp_async(host, CDN_FILES)
        except Exception as e:
            utils.log(e)

    def run(self):
        utils.log('running ...')
        for host in utils.CDN_HOSTS:
            self.run_cdn(host)
        self.run_dns(utils.DNS_HOST)
        utils.log('serving port', self.port)

    def run_dns(self, host):
        utils.log('host:', host)
        try:
            self.ssh(host, 'cd {}; make dns'.format(self.root))
            cmd = 'cd {}; ./dnsserver -d -p {} -n {} 2>err'
            self.ssh_async(host, cmd.format(self.root, self.port, self.name))
        except Exception as e:
            utils.log(e)

    def run_cdn(self, host):
        utils.log('host:', host)
        try:
            self.ssh(host, 'cd {}; make cdn'.format(self.root))
            cmd = 'cd {}; ./httpserver -d -p {} -o {} 2>err'
            self.ssh_async(host, cmd.format(self.root, self.port, self.origin))
        except Exception as e:
            utils.log(e)

    def stop(self):
        utils.log('stopping ...')
        self.stop_dns(utils.DNS_HOST)
        for host in utils.CDN_HOSTS:
            self.stop_cdn(host)
        utils.log('finished')

    def stop_dns(self, host):
        utils.log('host:', host)
        try:
            self.ssh(host, 'pkill python3.4')
        except Exception as e:
            utils.log(e)

    def stop_cdn(self, host):
        utils.log('host:', host)
        try:
            self.ssh(host, 'pkill python3.4')
        except Exception as e:
            utils.log(e)

    def scp_async(self, host, files):
        for f in files:
            p = subprocess.Popen(
                'scp -rp -i {} {} {}@{}:{}'.format(
                    self.keyfile,
                    f,
                    self.username,
                    host,
                    '{}/'.format(self.root), ),
                shell=True,
                stdout=subprocess.PIPE)
            self.procs.append(p)

    def ssh(self, host, cmd):
        subprocess.check_call(
            'ssh -i {} {}@{} "{}"'.format(
                self.keyfile,
                self.username,
                host,
                cmd, ),
            shell=True,
            stdout=subprocess.PIPE)

    def ssh_async(self, host, cmd):
        subprocess.check_call(
            'ssh -f -i {} {}@{} "{}"'.format(
                self.keyfile,
                self.username,
                host,
                cmd, ),
            shell=True,
            stdout=subprocess.PIPE)


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

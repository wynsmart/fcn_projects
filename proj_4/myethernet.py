import struct
from myarp import MyARP
import socket

class MyEthernet:

	def __init__(self):
		self.arp = MyARP()
		self.src_mac = arp.src_hwaddr
		self.dst_mac = arp.dst_hwaddr

	def _send(self):
		sock = socket.socket(AF_PACKET, SOCK_RAW)
		sock.bind('eth0', 0)
		sock.send(_build_packet())

	def _build_packet(self):
		eth_type = '0x0800'
		payload = None
		return self.dst_mac + self.src_mac + eth_type + payload

import socket
import struct
import json
import os

class Socket:
	def __init__(self, _globals):
		self.globals = _globals
		self.connected = False
		self.sock = None

		self.address = ("127.0.0.1", 5654)

	def close(self):
		try:
			self.sock.close()
		except:
			pass
		self.sock = None
		self.connected = False

	def connect(self):
		if self.connected:
			return True

		try:
			self.sock = socket.socket()
			self.sock.connect(self.address)
			self.connected = True

		except:
			self.close()
			return False

		sent = self.send({
			"type": "handshake",
			"token": os.getenv("FSOL_BOT_SOCKET_TOKEN")
		})
		if sent:
			recv = self.recv()

			if recv[0] and recv[1]["success"]:
				return True

		self.close()
		return False

	def send(self, data, *, recall=True):
		if self.connected:
			try:
				packet = json.dumps(data).encode()
				self.sock.send(struct.pack("!L", len(packet)) + packet)
				return True

			except:
				self.close()
				if recall and self.connect():
					return self.send(data, recall=False)
				return False
		else:
			if recall and self.connect():
				return self.send(data, recall=False)
			return False

	def recv(self, *, recall=True):
		if self.connected:
			try:
				length = struct.unpack("!L", self.sock.recv(4))
				packet = self.sock.recv(length[0])

				return True, json.loads(packet)

			except:
				self.close()
				if recall and self.connect():
					return self.recv(recall=False)
				return (False,)
		else:
			if recall and self.connect():
				return self.recv(recall=False)
			return (False,)

class CommunicationMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		if request.globals.socket is None:
			request.globals.socket = Socket(request.globals)

		return self.get_response(request)
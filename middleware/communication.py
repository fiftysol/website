import threading
import traceback
import socket
import struct
import queue
import json
import os

class Socket:
	def __init__(self):
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

class ScheduledCall:
	def __init__(self, **kwargs):
		self.call = None
		self.args = ()
		self.kwargs = {}
		self.resulted = False
		self.result = None

		for key, value in kwargs.items():
			setattr(self, key, value)

	def set_result(self, result):
		self.result = result
		self.resulted = True

	def wait_complete(self):
		while not self.resulted:
			pass

		return self.result

class SocketProcessing:
	def __init__(self, sock):
		self.sock = sock
		self.queue = queue.Queue()
		self.allow_send = True

	def send(self, *args, block_recv=False, **kwargs):
		while not self.allow_send:
			pass

		self.allow_send = False
		schedule = ScheduledCall(call=self.sock.send, args=args, kwargs=kwargs)
		self.queue.put(schedule)
		return schedule.wait_complete()

	def recv(self, *args, **kwargs):
		schedule = ScheduledCall(call=self.sock.recv, args=args, kwargs=kwargs)
		self.queue.put(schedule)
		self.allow_send = True
		return schedule.wait_complete()

	def loop(self):
		while True:
			obj = self.queue.get()

			try:
				result = obj.call(*obj.args, **obj.kwargs)
			except:
				traceback.print_exc()
				obj.set_result((False,))
			else:
				obj.set_result(result)

class CommunicationMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response
		self.processing = SocketProcessing(Socket())

		threading.Thread(target=self.processing.loop).start()

	def __call__(self, request):
		if request.globals.socket is None:
			request.globals.socket = self.processing

		return self.get_response(request)
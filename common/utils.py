import common.classes as classes
import requests
import base64
import json
import os

endpoint_key = os.getenv("FSOL_BOLO_ENDPOINT_KEY")

def send_and_recv(socket, data, deep=True, json=True):
	if socket is None:
		resp = "Socket instance was not initialized."
		if json:
			resp = classes.ErrorJSONResponse(resp, status=500)
		if deep:
			raise classes.DeepReturn(resp)
		return resp

	sent = socket.send(data)
	if not sent:
		resp = "Failed to connect to the gateway."
		if json:
			resp = classes.ErrorJSONResponse(resp, status=500)
		if deep:
			raise classes.DeepReturn(resp)
		return resp

	recv = socket.recv()
	if recv[0] and recv[1]["success"]:
		return recv[1]

	elif recv[0]:
		resp = "Gateway Error: " + recv[1]["error"]
		if json:
			resp = classes.ErrorJSONResponse(resp, status=500)
		if deep:
			raise classes.DeepReturn(resp)
		return resp

	else:
		resp = "Failed to receive data from the gateway."
		if json:
			resp = classes.ErrorJSONResponse(resp, status=500)
		if deep:
			raise classes.DeepReturn(resp)
		return resp

def endpoint_request(file):
	return requests.get(f"http://discbotdb.000webhostapp.com/get?k={endpoint_key}&f={file}").json()

def endpoint_save(file, data):
	return requests.post(
		f"http://discbotdb.000webhostapp.com/set?k={endpoint_key}&f={file}",
		data={
			"d": base64.b64encode(json.dumps(data))
		}
	)
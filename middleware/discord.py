import requests
import random
import time
import os

user_cache = []
max_cache_length = 100
cache_lifespan = 300

class DiscordUser:
	logged = False
	available_state_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
	data = {}

	def __init__(self, request):
		self.request = request
		self.load_data()

	def __str__(self):
		return f'<DiscordUser logged={self.logged} token={self.request.session["oauth2_token"] if "oauth2_token" in self.request.session else None} data={self.data}>'

	def generate_state(self, length=20):
		state = ""
		for iteration in range(length):
			state += random.choice(self.available_state_chars)

		return state

	def logout(self):
		self.logged = False

		if "oauth2_token" in self.request.session:
			rem = None
			for index, cache in enumerate(user_cache):
				if cache[0] == self.request.session["oauth2_token"]:
					rem = index
					break

			if rem is not None:
				user_cache.pop(rem)

			del self.request.session["oauth2_token"]

	def login(self, code):
		self.request.session["oauth2_code"] = code

		if self.create_token():
			self.load_data(refresh=True)
			return True
		return False

	def load_data(self, *, refresh=False):
		if not refresh:
			data = self.get_data()
		else:
			data = self.refresh_data()
		self.data = data

		if "from_cache" in data:
			del data["from_cache"]

		else:
			force_rem, rem = False, 0
			for index, cache in enumerate(user_cache):
				if cache[0] == self.request.session["oauth2_token"]:
					force_rem, rem = False, index
					break

			if force_rem or len(user_cache) >= max_cache_length:
				user_cache.pop(rem)

			user_cache.append([self.request.session["oauth2_token"], time.time() + cache_lifespan, data])

		for field, value in data.items():
			if field == "username":
				self.username = value
				self.name = value

			else:
				setattr(self, field, value)

		if self.logged:
			self.full_name = self.name + "#" + self.discriminator

			if self.avatar is None:
				self.avatar_endpoint = f"embed/avatars/{int(self.id) % 5}"

			else:
				self.avatar_endpoint = f'avatars/{self.id}/{self.avatar}'

		else:
			self.avatar_endpoint = "embed/avatars/0"

	def get_data(self):
		if "oauth2_token" in self.request.session:
			rem = None
			for index, cache in enumerate(user_cache):
				if cache[0] == self.request.session["oauth2_token"]:
					if time.time() <= cache[1]:
						cache[2]["from_cache"] = True
						return cache[2]
					else:
						rem = index
					break

			if rem is not None:
				user_cache.pop(rem)

			return self.refresh_data()

		return {"logged": False, "from_cache": True}

	def refresh_data(self):
		if "oauth2_token" in self.request.session:
			response = requests.get(
				"https://discordapp.com/api/users/@me",
				headers={
					"Authorization": self.request.session["oauth2_token"]["token_type"] + " " + self.request.session["oauth2_token"]["access_token"]
				}
			)

			if response.status_code == 200:
				data = response.json()
				data["logged"] = True
				return data
			return {"logged": False, "from_cache": True}

		return {"logged": False, "from_cache": True}

	def create_token(self):
		if "oauth2_token" in self.request.session:
			response = requests.post("https://discordapp.com/api/oauth2/token", data={
				"client_id": os.getenv("FSOL_OAUTH2_CLIENT_ID"),
				"client_secret": os.getenv("FSOL_OAUTH2_CLIENT_SECRET"),
				"grant_type": "refresh_token",
				"refresh_token": self.request.session["oauth2_token"]["refresh_token"],
				"redirect_uri": "http://" + self.request.globals.host + "/api/oauth2/authorized/",
				"scope": "identify"
			}, headers={"Content-Type": "application/x-www-form-urlencoded"})

			if response.status_code == 200:
				self.request.session["oauth2_token"] = response.json()
				return True

			else:
				del self.request.session["oauth2_token"]

		elif "oauth2_code" in self.request.session:
			response = requests.post("https://discordapp.com/api/oauth2/token", data={
				"client_id": os.getenv("FSOL_OAUTH2_CLIENT_ID"),
				"client_secret": os.getenv("FSOL_OAUTH2_CLIENT_SECRET"),
				"grant_type": "authorization_code",
				"code": self.request.session["oauth2_code"],
				"redirect_uri": "http://" + self.request.globals.host + "/api/oauth2/authorized/",
				"scope": "identify"
			}, headers={"Content-Type": "application/x-www-form-urlencoded"})

			del self.request.session["oauth2_code"]
			if response.status_code == 200:
				self.request.session["oauth2_token"] = response.json()
				return True

		return False

class DiscordMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		request.discord = DiscordUser(request)
		request.user = request.discord

		return self.get_response(request)
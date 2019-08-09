from django.http import HttpResponse
from django.conf import settings
from django.urls import re_path

from django.shortcuts import render
from .classes import DeepReturn
from .utils import send_and_recv

import translation.backend as translation
import time
import os
import re

def as_color(color):
	h = hex(color)[2:]
	return "0" * (6 - len(h)) + h

def dropdown_menu_items(request, context):
	has = {"Module Member": False, "Developer": False, "Translator": False}
	is_member = False
	has_any_role = False
	if request.user.logged:
		try:
			data = send_and_recv(request.globals.socket, {
				"type": "user_roles",
				"user": request.user.id
			}, json=False)
		except DeepReturn:
			context["in_server"] = False
		else:
			if data["in_server"]:
				is_member = True
				context["in_server"] = True
				context["user_role_ids"] = data["role_ids"]
				context["user_roles"] = list(map(lambda role: (role[0], as_color(role[1])), data["role_colors"]))
				context["user_color"] = data["color"]
			else:
				context["in_server"] = False
			for role in has:
				if role in data["role_names"]:
					has_any_role = True
					has[role] = True

	return (
		{
			"show": is_member,
			"type": "header",
			"text": context["translate"]["member"].upper()
		},
		{
			"show": is_member,
			"type": "link",
			"link": "/members/@me/",
			"text": context["translate"]["my_profile"]
		},
		{
			"show": has["Module Member"],
			"type": "separator"
		},
		{
			"show": has["Module Member"],
			"type": "header",
			"link": "#",
			"text": context["translate"]["module_member"].upper()
		},
		{
			"show": has["Module Member"],
			"type": "link",
			"link": "#",
			"text": context["translate"]["my_commands"]
		},
		{
			"show": has["Module Member"],
			"type": "link",
			"link": "#",
			"text": context["translate"]["my_modules"]
		},
		{
			"show": has["Developer"],
			"type": "separator"
		},
		{
			"show": has["Developer"],
			"type": "header",
			"text": context["translate"]["developer"].upper()
		},
		{
			"show": has["Developer"],
			"type": "link",
			"link": "#",
			"text": context["translate"]["my_projects"]
		},
		{
			"show": has["Developer"],
			"type": "link",
			"link": "#",
			"text": context["translate"]["new_project"]
		},
		{
			"show": has["Translator"],
			"type": "separator"
		},
		{
			"show": has["Translator"],
			"type": "header",
			"text": context["translate"]["translator"].upper()
		},
		{
			"show": has["Translator"],
			"type": "link",
			"link": "#",
			"text": context["translate"]["translation_panel"]
		},
		{
			"show": is_member or has_any_role,
			"type": "separator"
		},
		{
			"show": True,
			"type": "link",
			"link": "/api/oauth2/logout",
			"text": context["translate"]["logout"]
		},
	)

class Static:
	content_types = {
		"css": "text/css",
		"csv": "text/csv",
		"html": "text/html",

		"mp4": "video/mp4",

		"gif": "image/gif",
		"png": "image/png",
		"jpg": "image/jpeg",
		"jpeg": "image/jpeg",
		"webp": "image/webp",

		"js": "application/javascript",
		"ogg": "application/ogg",
		"zip": "application/zip",
		"pdf": "application/pdf",
		"xml": "application/xml",
		"json": "application/json"
	}

	def get_file(self, dir, file):
		with open(os.path.join(dir, file), "rb") as obj:
			file = os.path.basename(file)
			content_type = "text/plain"

			if "." in file:
				extension = file.split(".")[-1].lower()

				if extension in self.content_types:
					content_type = self.content_types[extension]

			return HttpResponse(obj.read(), content_type=content_type)

	def view(self, request, *, path):
		path = path.replace("\\", "/")
		if path == ".." or path.startswith("../") or "/../" in path:
			return HttpResponse("404 Not Found", content_type="text/plain", status=404)

		try:
			return self.get_file(settings.STATIC_ROOT, path)
		except FileNotFoundError:
			return HttpResponse("404 Not Found", content_type="text/plain", status=404)
		except:
			return HttpResponse("500 Server Error", content_type="text/plain", status=500)

class TranslationDictWrapper:
	def __init__(self, data):
		self.data = data

	def __getitem__(self, key):
		return self.data.get(key, f"%{key}%")

class TemplateRenderer:
	template = None
	regex = ""
	args = []
	kwargs = {}
	context = {}
	content_type = None
	status = None
	using = None
	dont_translate = False

	def as_url(self):
		if self.template is None:
			raise NotImplementedError("TemplateRenderer.as_url requires TemplateRenderer.template not to be None.")

		return re_path(self.regex, self.view, *self.args, **self.kwargs)

	def before(self, request, context):
		return request, context

	def after(self, request, rendered, context):
		return rendered

	def view(self, request, **kwargs):
		context = self.context.copy()

		context["request"] = request
		for key, value in kwargs.items():
			context[key] = value

		context["welcome_user"] = False
		context["right_now"] = time.time()

		if request.user.logged:
			if "welcomed" not in request.session or not request.session["welcomed"]:
				request.session["welcomed"] = True
				context["welcome_user"] = True

		if not self.dont_translate:
			translate = translation.get_fields(translation.get_language_from_request("@website", request), apply_default=True)
			context["translate_v"] = TranslationDictWrapper(translate[0])
			context["translate"] = TranslationDictWrapper(translate[1])

		request, context = self.before(request, context)
		if not "dropdown_menu_items" in context:
			context["dropdown_menu_items"] = dropdown_menu_items(request, context)
		rendered = render(request, self.template, context=context, content_type=self.content_type, status=self.status, using=self.using)
		return self.after(request, rendered, context)

class HomeTemplate(TemplateRenderer):
	template = "home/index.html"
	regex = r"^/*$"
	context = {
		"where": "home",
		"member_role_check": [
			["Module Member", "https://cdn.discordapp.com/emojis/456198795768889344.png?size=32"],
			["Developer", "https://cdn.discordapp.com/emojis/468936022248390687.png?size=32"],
			["Artist", "https://cdn.discordapp.com/emojis/468937377981923339.png?size=32"],
			["Translator", "https://discordapp.com/assets/487af9f8669d2659ceb859f6dc7d2983.svg"],
			["Mapper", "https://cdn.discordapp.com/emojis/463508055577985024.png?size=32"],
			["Event Manager", "https://cdn.discordapp.com/emojis/559070151278854155.png?size=32"],
			["Shades Helper", "https://cdn.discordapp.com/emojis/542115872328646666.png?size=32"],
			["Funcorp", "https://cdn.discordapp.com/emojis/559069782469771264.png?size=32"],
			["Mathematician", "https://discordapp.com/assets/b43c5c7f3fd21d04273303bc0db9cc02.svg"],
			["Fashionista", "https://cdn.discordapp.com/emojis/468937918115741718.png?size=32"],
			["Writer", "https://discordapp.com/assets/a77e0fdf1c1dddb8de08f3b67a971bff.svg"],
		]
	}

	def before(self, request, context):
		try:
			data1 = send_and_recv(request.globals.socket, {
				"type": "fetch_announcements",
				"small": False,
				"page": 0
			}, json=False)

			data2 = send_and_recv(request.globals.socket, {
				"type": "fetch_announcements",
				"small": True,
				"page": 0
			}, json=False)

			data3 = send_and_recv(request.globals.socket, {
				"type": "get_member_profiles",
				"users": 5
			}, json=False)
		except DeepReturn:
			context["announcements"] = []
			context["sample_members"] = []
		else:
			big = data1["messages"][0]
			small = data2["messages"][0]

			big["small"] = False
			small["small"] = True

			big["color"] = as_color(big["color"])
			small["color"] = as_color(small["color"])

			context["announcements"] = [big, small]

			context["sample_members"] = data3["users"]
			for id, member in context["sample_members"].items():
				member["discord"]["color"] = as_color(member["discord"]["color"])
				member["id"] = id
			context["sample_members"] = context["sample_members"].values()

		return request, context

class AnnouncementsTemplate(TemplateRenderer):
	template = "announcements/index.html"
	regex = r"(?i)^announcements/*$"
	context = {
		"where": "announcements",
		"available_pages": list(range(5))
	}

class MembersTemplate(TemplateRenderer):
	template = "members/index.html"
	regex = r"(?i)^members/*$"
	context = {
		"where": "members"
	}

	def before(self, request, context):
		try:
			data1 = send_and_recv(request.globals.socket, {
				"type": "get_member_profiles_quantity"
			})

			data2 = send_and_recv(request.globals.socket, {
				"type": "get_member_profiles",
				"users": 1000
			}, json=False)
		except DeepReturn:
			context["sample_members"] = []
		else:
			context["member_quantity"] = data1["quantity"]

			context["sample_members"] = data2["users"]
			for id, member in context["sample_members"].items():
				if member is not None:
					member["discord"]["color"] = as_color(member["discord"]["color"])
					member["id"] = id

			context["sample_members"] = context["sample_members"].values()

		return request, context

class SpecificMemberTemplate(TemplateRenderer):
	template = "members/member.html"
	regex = r"(?i)^members/+(?P<mid>.+?)(?:/*|/+.*)$"
	context = {
		"where": "members",
		"member_role_check": [
			"Module Member",
			"Developer",
			"Artist",
			"Translator",
			"Mapper",
			"Event Manager",
			"Shades Helper",
			"Funcorp",
			"Mathematician",
			"Fashionista",
			"Writer",
		]
	}

	def before(self, request, context):
		_member = context["mid"]
		if _member.isdigit() or (_member == "@me" and request.user.logged):
			if _member == "@me":
				_member = request.user.id
			try:
				data = send_and_recv(request.globals.socket, {
					"type": "get_member_profiles",
					"users": [_member]
				})
			except DeepReturn:
				if _member == request.user.id:
					context["dropdown_menu_items"] = dropdown_menu_items(request, context)
					if context["in_server"]:
						context["member"] = {
							"id": request.user.id,
							"discord": {
								"name": request.user.name,
								"color": as_color(context["user_color"]),
								"avatar": request.user.avatar_endpoint,
								"roles": context["user_roles"],
								"is_mod": "585148219395276801" in context["user_role_ids"]
							}
						}
			else:
				member = data["users"][_member]
				if member:
					member["discord"]["color"] = as_color(member["discord"]["color"])
					member["id"] = _member
					member["roles"] = [("Moderator", "999999")] if member["discord"]["is_mod"] else []
					for role in reversed(member["discord"]["roles"]):
						role[1] = as_color(role[1])
						if role[0] in context["member_role_check"]:
							member["roles"].append(role)
					context["member"] = member

		if "member" in context and "status" in context["member"]:
			context["member"]["status"] = context["member"]["status"].replace("&", "&amp;").replace("<", "&lt;")
		# 	context["member"]["status"] = re.sub(r"`([^`]+?)`", r'<code class="inline">\1</code>', context["member"]["status"])
		# 	context["member"]["status"] = re.sub(r"\*\*(.+?)\*\*", r'<strong>\1</strong>', context["member"]["status"])
		# 	context["member"]["status"] = re.sub(r"__(.+?)__", r'<u>\1</u>', context["member"]["status"])
		# 	context["member"]["status"] = re.sub(r"~~(.+?)~~", r'<s>\1</s>', context["member"]["status"])
		# 	context["member"]["status"] = re.sub(r"(_|\*)(.+?)\1", r'<em>\2</em>', context["member"]["status"])

		return request, context